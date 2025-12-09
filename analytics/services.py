# analytics/services.py

from typing import Dict, List, Any
from datetime import datetime, timedelta
import hashlib
import json
from django.db.models import Count, Sum, Avg, Max, Min, Q
from .models import Visualization, AnalyticsCache
from surveys.models import Survey, SurveyData
from indicators.models import Indicator, IndicatorValue

class AnalyticsEngine:
    """
    Core analytics engine - similar to DHIS2's analytics engine
    Handles data aggregation, dimension processing, and result formatting
    """
    
    def __init__(self, project_id: int):
        self.project_id = project_id
    
    def evaluate_visualization(self, visualization: Visualization) -> Dict[str, Any]:
        """
        Evaluate a visualization and return formatted results
        """
        # Check cache first
        cache_key = self._generate_cache_key(visualization)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # Extract dimensions
        dimensions = visualization.dimensions
        filters = visualization.filters
        layout = visualization.layout
        
        # Get data based on dimensions
        data = self._fetch_data(dimensions, filters)
        
        # Aggregate data
        aggregated = self._aggregate_data(data, layout)
        
        # Format for visualization type
        formatted = self._format_for_visualization(
            aggregated, 
            visualization.visualization_type,
            visualization.display_options
        )
        
        # Cache result
        self._save_to_cache(cache_key, formatted, visualization)
        
        return formatted
    
    def _fetch_data(self, dimensions: Dict, filters: Dict) -> List[Dict]:
        """
        Fetch raw data based on dimensions and filters
        """
        data_items = dimensions.get('data', [])  # Indicator IDs
        period = dimensions.get('period', {})

        if not data_items:
            print("No data items (indicators) specified")
            return []

        # Get indicator values for this project
        # Filter by both indicator project and survey project for double security
        query = IndicatorValue.objects.filter(
            indicator_id__in=data_items,
            indicator__project_id=self.project_id,
            survey__project_id=self.project_id
        )

        print(f"Fetching data for indicators: {data_items}, project: {self.project_id}")
        print(f"Initial query count: {query.count()}")

        # Apply period filter
        if period.get('type') == 'relative':
            query = self._apply_relative_period(query, period.get('value'))
            print(f"After period filter: {query.count()}")

        # Apply additional filters
        for key, value in filters.items():
            # Apply filters based on survey data
            pass

        data = list(query.values(
            'indicator__name',
            'indicator_id',
            'value',
            'period',
            'calculated_at',
            'survey__name'
        ))

        print(f"Fetched {len(data)} indicator values: {data}")

        return data
    
    def _aggregate_data(self, data: List[Dict], layout: Dict) -> Dict:
        """
        Aggregate data based on layout configuration
        """
        if not data:
            print("No data to aggregate")
            return {}

        rows = layout.get('rows', [])
        columns = layout.get('columns', [])

        # Group data by rows and columns
        aggregated = {}

        for item in data:
            row_key = self._get_dimension_key(item, rows)
            col_key = self._get_dimension_key(item, columns)

            key = f"{row_key}_{col_key}"
            if key not in aggregated:
                aggregated[key] = {
                    'row': row_key,
                    'column': col_key,
                    'values': []
                }

            aggregated[key]['values'].append(item['value'])

        # Calculate aggregates (sum, avg, etc.)
        for key in aggregated:
            values = aggregated[key]['values']
            aggregated[key]['sum'] = sum(values)
            aggregated[key]['avg'] = sum(values) / len(values) if values else 0
            aggregated[key]['count'] = len(values)

        print(f"Aggregated data: {aggregated}")

        return aggregated
    
    def _format_for_visualization(
        self, 
        data: Dict, 
        viz_type: str,
        display_options: Dict
    ) -> Dict:
        """
        Format aggregated data for specific visualization type
        """
        if viz_type in ['column_chart', 'bar_chart', 'line_chart', 'area_chart']:
            return self._format_for_chart(data, viz_type, display_options)
        elif viz_type == 'pivot_table':
            return self._format_for_pivot(data, display_options)
        elif viz_type == 'pie_chart':
            return self._format_for_pie(data, display_options)
        elif viz_type == 'single_value':
            return self._format_for_single_value(data, display_options)
        else:
            return data
    
    def _format_for_chart(self, data: Dict, chart_type: str, options: Dict) -> Dict:
        """
        Format data for Recharts
        """
        chart_data = []

        for key, item in data.items():
            chart_data.append({
                'name': item['row'],
                'value': item['sum'],
                'average': item['avg'],
                'count': item['count']
            })

        # Add default labels if not provided
        if 'xAxisLabel' not in options:
            options['xAxisLabel'] = 'Period'
        if 'yAxisLabel' not in options:
            options['yAxisLabel'] = 'Value'

        return {
            'type': chart_type,
            'data': chart_data,
            'options': options
        }
    
    def _format_for_pivot(self, data: Dict, options: Dict) -> Dict:
        """
        Format data for pivot table
        """
        rows = set()
        columns = set()

        for item in data.values():
            rows.add(item['row'])
            columns.add(item['column'])

        pivot_data = {
            'rows': sorted(list(rows)),
            'columns': sorted(list(columns)),
            'data': data,
            'options': options
        }

        return pivot_data

    def _format_for_pie(self, data: Dict, options: Dict) -> Dict:
        """
        Format data for pie chart
        """
        pie_data = []

        for key, item in data.items():
            pie_data.append({
                'name': item['row'],
                'value': item['sum']
            })

        return {
            'type': 'pie_chart',
            'data': pie_data,
            'options': options
        }

    def _format_for_single_value(self, data: Dict, options: Dict) -> Dict:
        """
        Format data for single value display
        """
        # Calculate total/average from all data
        total_sum = 0
        total_count = 0

        for item in data.values():
            total_sum += item['sum']
            total_count += item['count']

        avg_value = total_sum / total_count if total_count > 0 else 0

        # Get target from options if available
        target = options.get('target_value')

        # Calculate trend (placeholder - would need historical data)
        trend = options.get('trend', 0)

        return {
            'type': 'single_value',
            'data': {
                'value': total_sum,
                'label': options.get('label', 'Total'),
                'trend': trend,
                'target': target,
                'average': avg_value
            },
            'options': options
        }
    
    def _generate_cache_key(self, visualization: Visualization) -> str:
        """
        Generate unique cache key for visualization
        """
        key_data = {
            'viz_id': visualization.id if hasattr(visualization, 'id') and visualization.id else 'preview',
            'dimensions': visualization.dimensions,
            'filters': visualization.filters,
            'updated_at': visualization.updated_at.isoformat() if hasattr(visualization, 'updated_at') and visualization.updated_at else 'preview'
        }

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Dict | None:
        """
        Retrieve from cache if not expired
        """
        try:
            cache = AnalyticsCache.objects.get(
                cache_key=cache_key,
                expires_at__gt=datetime.now()
            )
            cache.hit_count += 1
            cache.save()
            return cache.data
        except AnalyticsCache.DoesNotExist:
            return None
    
    def _save_to_cache(self, cache_key: str, data: Dict, visualization: Visualization):
        """
        Save to cache with expiration
        """
        # Only cache if visualization is saved (has an id)
        if not hasattr(visualization, 'id') or visualization.id is None:
            return

        expires_at = datetime.now() + timedelta(hours=24)

        AnalyticsCache.objects.update_or_create(
            cache_key=cache_key,
            defaults={
                'project_id': self.project_id,
                'visualization': visualization,
                'data': data,
                'expires_at': expires_at
            }
        )
    
    def _apply_relative_period(self, query, period_value: str):
        """
        Apply relative period filters (LAST_12_MONTHS, THIS_YEAR, etc.)
        """
        # Implementation for relative periods
        return query
    
    def _get_dimension_key(self, item: Dict, dimensions: List[str]) -> str:
        """
        Generate key from dimension values
        """
        return "_".join([str(item.get(dim, '')) for dim in dimensions])