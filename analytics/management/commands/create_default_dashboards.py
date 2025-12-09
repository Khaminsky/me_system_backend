# analytics/management/commands/create_default_dashboards.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from analytics.models import Dashboard, Visualization, DashboardItem
from projects.models import Project
from indicators.models import Indicator

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default dashboard templates for projects'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='Create dashboard for specific project ID',
        )
    
    def handle(self, *args, **options):
        project_id = options.get('project_id')
        
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                projects = [project]
            except Project.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Project with ID {project_id} not found'))
                return
        else:
            projects = Project.objects.all()
        
        created_count = 0
        
        for project in projects:
            # Check if default dashboard already exists
            if Dashboard.objects.filter(project=project, is_default=True).exists():
                self.stdout.write(
                    self.style.WARNING(f'Default dashboard already exists for {project.name}')
                )
                continue
            
            # Get project admin or first user
            admin_user = project.created_by or User.objects.first()
            
            # Create default dashboard
            dashboard = Dashboard.objects.create(
                project=project,
                name='Overview Dashboard',
                description='Project overview with key metrics and visualizations',
                is_default=True,
                created_by=admin_user
            )
            
            # Get project indicators
            indicators = Indicator.objects.filter(project=project)[:5]  # Top 5 indicators
            
            if indicators.exists():
                # Create visualizations for each indicator type
                position_y = 0
                
                # 1. Single Value - Total Indicators
                viz_summary = Visualization.objects.create(
                    project=project,
                    name='Key Metrics Summary',
                    description='Summary of key project metrics',
                    visualization_type='single_value',
                    dimensions={
                        'data': [ind.id for ind in indicators],
                        'period': {'type': 'relative', 'value': 'LAST_12_MONTHS'}
                    },
                    filters={},
                    layout={'rows': ['period'], 'columns': ['data'], 'filters': []},
                    display_options={
                        'show_legend': False,
                        'label': 'Total Value',
                        'colors': ['#3b82f6']
                    },
                    created_by=admin_user
                )
                
                DashboardItem.objects.create(
                    dashboard=dashboard,
                    visualization=viz_summary,
                    position_x=0,
                    position_y=position_y,
                    width=4,
                    height=3,
                    order=1
                )
                
                # 2. Column Chart - Indicators Over Time
                viz_chart = Visualization.objects.create(
                    project=project,
                    name='Indicators Trend',
                    description='Indicator values over time',
                    visualization_type='column_chart',
                    dimensions={
                        'data': [ind.id for ind in indicators],
                        'period': {'type': 'relative', 'value': 'LAST_6_MONTHS'}
                    },
                    filters={},
                    layout={'rows': ['period'], 'columns': ['data'], 'filters': []},
                    display_options={
                        'show_legend': True,
                        'show_values': True,
                        'colors': ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']
                    },
                    created_by=admin_user
                )
                
                DashboardItem.objects.create(
                    dashboard=dashboard,
                    visualization=viz_chart,
                    position_x=4,
                    position_y=position_y,
                    width=8,
                    height=4,
                    order=2
                )
                
                position_y += 4
                
                # 3. Pie Chart - Indicator Distribution
                viz_pie = Visualization.objects.create(
                    project=project,
                    name='Indicator Distribution',
                    description='Distribution of indicator values',
                    visualization_type='pie_chart',
                    dimensions={
                        'data': [ind.id for ind in indicators],
                        'period': {'type': 'relative', 'value': 'THIS_YEAR'}
                    },
                    filters={},
                    layout={'rows': ['data'], 'columns': [], 'filters': ['period']},
                    display_options={
                        'show_legend': True,
                        'colors': ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']
                    },
                    created_by=admin_user
                )
                
                DashboardItem.objects.create(
                    dashboard=dashboard,
                    visualization=viz_pie,
                    position_x=0,
                    position_y=position_y,
                    width=6,
                    height=4,
                    order=3
                )
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created default dashboard for {project.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'No indicators found for {project.name}. Dashboard created but empty.'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} default dashboard(s)')
        )

