# analytics/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Visualization, Dashboard, DashboardItem, DataDimension
from .serializers import (
    VisualizationSerializer, 
    DashboardSerializer,
    DashboardItemSerializer,
    DataDimensionSerializer
)
from .services import AnalyticsEngine
from projects.models import Project

class VisualizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for visualizations
    """
    serializer_class = VisualizationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        if project_id:
            return Visualization.objects.filter(project_id=project_id, is_active=True)
        return Visualization.objects.filter(is_active=True)
    
    @action(detail=True, methods=['get'])
    def evaluate(self, request, pk=None):
        """
        Evaluate visualization and return data
        GET /api/analytics/visualizations/{id}/evaluate/
        """
        visualization = self.get_object()
        engine = AnalyticsEngine(visualization.project_id)
        
        try:
            result = engine.evaluate_visualization(visualization)
            return Response(result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def preview(self, request):
        """
        Preview visualization without saving
        POST /api/analytics/visualizations/preview/
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create temporary visualization (don't save)
        temp_viz = Visualization(**serializer.validated_data)
        engine = AnalyticsEngine(temp_viz.project_id)

        try:
            result = engine.evaluate_visualization(temp_viz)
            return Response(result)
        except Exception as e:
            import traceback
            return Response(
                {'error': str(e), 'traceback': traceback.format_exc()},
                status=status.HTTP_400_BAD_REQUEST
            )
        # analytics/views.py - Add to VisualizationViewSet

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """
        Export visualization data to Excel/CSV
        GET /api/analytics/visualizations/{id}/export/?format=csv
        GET /api/analytics/visualizations/{id}/export/?format=excel
        """
        import csv
        import io
        from django.http import HttpResponse

        visualization = self.get_object()
        engine = AnalyticsEngine(visualization.project_id)
        result = engine.evaluate_visualization(visualization)

        format_type = request.query_params.get('format', 'csv')

        if format_type == 'excel':
            # Generate Excel file
            try:
                import openpyxl
                from openpyxl import Workbook

                wb = Workbook()
                ws = wb.active
                ws.title = visualization.name[:31]  # Excel sheet name limit

                # Write headers
                if result.get('type') in ['column_chart', 'bar_chart', 'line_chart', 'area_chart', 'pie_chart']:
                    data = result.get('data', [])
                    if data:
                        headers = list(data[0].keys())
                        ws.append(headers)

                        # Write data rows
                        for row in data:
                            ws.append([row.get(h) for h in headers])

                elif result.get('rows') and result.get('columns'):
                    # Pivot table format
                    rows = result.get('rows', [])
                    columns = result.get('columns', [])
                    data_dict = result.get('data', {})

                    # Write header row
                    ws.append([''] + columns)

                    # Write data rows
                    for row in rows:
                        row_data = [row]
                        for col in columns:
                            key = f"{row}_{col}"
                            cell_data = data_dict.get(key, {})
                            row_data.append(cell_data.get('sum', 0))
                        ws.append(row_data)

                # Save to BytesIO
                output = io.BytesIO()
                wb.save(output)
                output.seek(0)

                response = HttpResponse(
                    output.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{visualization.name}.xlsx"'
                return response

            except ImportError:
                return Response(
                    {'error': 'openpyxl library not installed. Install with: pip install openpyxl'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        elif format_type == 'csv':
            # Generate CSV file
            output = io.StringIO()
            writer = csv.writer(output)

            # Write data based on visualization type
            if result.get('type') in ['column_chart', 'bar_chart', 'line_chart', 'area_chart', 'pie_chart']:
                data = result.get('data', [])
                if data:
                    headers = list(data[0].keys())
                    writer.writerow(headers)

                    for row in data:
                        writer.writerow([row.get(h) for h in headers])

            elif result.get('rows') and result.get('columns'):
                # Pivot table format
                rows = result.get('rows', [])
                columns = result.get('columns', [])
                data_dict = result.get('data', {})

                # Write header row
                writer.writerow([''] + columns)

                # Write data rows
                for row in rows:
                    row_data = [row]
                    for col in columns:
                        key = f"{row}_{col}"
                        cell_data = data_dict.get(key, {})
                        row_data.append(cell_data.get('sum', 0))
                    writer.writerow(row_data)

            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{visualization.name}.csv"'
            return response

        else:
            return Response(
                {'error': f'Unsupported format: {format_type}. Use "csv" or "excel"'},
                status=status.HTTP_400_BAD_REQUEST
            )
    

class DashboardViewSet(viewsets.ModelViewSet):
    """
    API endpoint for dashboards
    """
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        if project_id:
            return Dashboard.objects.filter(project_id=project_id)
        return Dashboard.objects.all()
    
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """
        Get dashboard with all visualization data evaluated
        GET /api/analytics/dashboards/{id}/data/
        """
        dashboard = self.get_object()
        engine = AnalyticsEngine(dashboard.project_id)
        
        items = []
        for item in dashboard.items.all():
            viz_data = engine.evaluate_visualization(item.visualization)
            items.append({
                'id': item.id,
                'visualization': {
                    'id': item.visualization.id,
                    'name': item.visualization.name,
                    'type': item.visualization.visualization_type,
                },
                'position': {
                    'x': item.position_x,
                    'y': item.position_y,
                    'w': item.width,
                    'h': item.height
                },
                'data': viz_data
            })
        
        return Response({
            'dashboard': DashboardSerializer(dashboard).data,
            'items': items
        })

    @action(detail=True, methods=['post'])
    def add_visualization(self, request, pk=None):
        """
        Add a visualization to the dashboard
        POST /api/analytics/dashboards/{id}/add_visualization/
        Body: {
            "visualization": <viz_id>,
            "position": {"x": 0, "y": 0, "w": 6, "h": 4}
        }
        """
        from .models import DashboardItem

        dashboard = self.get_object()
        visualization_id = request.data.get('visualization')
        position = request.data.get('position', {})

        if not visualization_id:
            return Response(
                {'error': 'visualization field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create dashboard item
        item = DashboardItem.objects.create(
            dashboard=dashboard,
            visualization_id=visualization_id,
            position_x=position.get('x', 0),
            position_y=position.get('y', 0),
            width=position.get('w', 6),
            height=position.get('h', 4)
        )

        return Response({
            'id': item.id,
            'message': 'Visualization added to dashboard successfully'
        }, status=status.HTTP_201_CREATED)


class ProjectAnalyticsView(viewsets.ViewSet):
    """
    Project-specific analytics endpoints
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get analytics summary for a project
        GET /api/analytics/projects/summary/?project_id=1
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {'error': 'project_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        project = get_object_or_404(Project, id=project_id)
        
        # Get summary statistics
        summary = {
            'project': {
                'id': project.id,
                'name': project.name
            },
            'surveys': project.surveys.count(),
            'indicators': project.indicators.count(),
            'visualizations': project.visualizations.count(),
            'dashboards': project.dashboards.count(),
        }
        
        return Response(summary)