# analytics/models.py

from django.db import models
from django.conf import settings
from projects.models import Project
from surveys.models import Survey
from indicators.models import Indicator

class Visualization(models.Model):
    """
    DHIS2-style visualization configuration
    Similar to DHIS2's Visualization object
    """
    VISUALIZATION_TYPES = [
        ('pivot_table', 'Pivot Table'),
        ('column_chart', 'Column Chart'),
        ('bar_chart', 'Bar Chart'),
        ('line_chart', 'Line Chart'),
        ('area_chart', 'Area Chart'),
        ('pie_chart', 'Pie Chart'),
        ('gauge', 'Gauge'),
        ('single_value', 'Single Value'),
        ('scatter', 'Scatter Plot'),
        ('radar', 'Radar Chart'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='visualizations')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    visualization_type = models.CharField(max_length=50, choices=VISUALIZATION_TYPES)
    
    # Dimensions configuration (DHIS2 concept)
    dimensions = models.JSONField(
        default=dict,
        help_text="""
        {
            "data": ["indicator_id_1", "indicator_id_2"],  # Data dimension
            "period": {"type": "relative", "value": "LAST_12_MONTHS"},  # Period dimension
            "orgUnit": {"type": "project", "value": "project_id"},  # Org unit dimension
            "disaggregation": ["gender", "age_group"]  # Category dimensions
        }
        """
    )
    
    # Filters (items not shown in rows/columns but filter the data)
    filters = models.JSONField(
        default=dict,
        help_text='{"region": "North", "status": "Active"}'
    )
    
    # Layout configuration
    layout = models.JSONField(
        default=dict,
        help_text="""
        {
            "rows": ["period"],
            "columns": ["data", "disaggregation"],
            "filters": ["orgUnit"]
        }
        """
    )
    
    # Display options
    display_options = models.JSONField(
        default=dict,
        help_text="""
        {
            "show_legend": true,
            "show_values": true,
            "target_line": true,
            "trend_line": false,
            "colors": ["#3b82f6", "#ef4444", "#10b981"]
        }
        """
    )
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.visualization_type})"


class Dashboard(models.Model):
    """
    Project-specific dashboard containing multiple visualizations
    Similar to DHIS2's Dashboard
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='dashboards')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Dashboard layout (grid-based)
    layout = models.JSONField(
        default=list,
        help_text="""
        [
            {"visualization_id": 1, "x": 0, "y": 0, "w": 6, "h": 4},
            {"visualization_id": 2, "x": 6, "y": 0, "w": 6, "h": 4}
        ]
        """
    )
    
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['project', 'name']
    
    def __str__(self):
        return f"{self.project.name} - {self.name}"


class DashboardItem(models.Model):
    """
    Individual items on a dashboard
    """
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='items')
    visualization = models.ForeignKey(Visualization, on_delete=models.CASCADE)
    
    # Position and size in grid
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=6)  # Grid columns (out of 12)
    height = models.IntegerField(default=4)  # Grid rows
    
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'position_y', 'position_x']
    
    def __str__(self):
        return f"{self.dashboard.name} - {self.visualization.name}"


class AnalyticsCache(models.Model):
    """
    Cache computed analytics results for performance
    Similar to DHIS2's analytics tables
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='analytics_cache')
    visualization = models.ForeignKey(Visualization, on_delete=models.CASCADE, null=True, blank=True)
    
    # Cache key (hash of query parameters)
    cache_key = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Cached data
    data = models.JSONField()
    metadata = models.JSONField(default=dict)
    
    # Cache metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    hit_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cache_key', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Cache: {self.cache_key}"


class DataDimension(models.Model):
    """
    Define reusable data dimensions for analytics
    (e.g., Age Groups, Gender, Regions)
    """
    DIMENSION_TYPES = [
        ('category', 'Category'),
        ('indicator_group', 'Indicator Group'),
        ('period', 'Period'),
        ('orgunit', 'Organisation Unit'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='dimensions')
    name = models.CharField(max_length=255)
    dimension_type = models.CharField(max_length=50, choices=DIMENSION_TYPES)
    
    # Dimension items (e.g., ["Male", "Female"] for Gender)
    items = models.JSONField(
        default=list,
        help_text='[{"id": "male", "name": "Male"}, {"id": "female", "name": "Female"}]'
    )
    
    # Mapping to survey fields
    field_mapping = models.JSONField(
        default=dict,
        help_text='{"survey_field": "gender", "value_mapping": {"M": "male", "F": "female"}}'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.dimension_type})"


class FavoriteVisualization(models.Model):
    """
    User's favorite visualizations for quick access
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_visualizations')
    visualization = models.ForeignKey(Visualization, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'visualization']
        ordering = ['-created_at']