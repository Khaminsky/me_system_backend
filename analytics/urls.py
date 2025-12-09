# analytics/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VisualizationViewSet, DashboardViewSet, ProjectAnalyticsView

router = DefaultRouter()
router.register(r'visualizations', VisualizationViewSet, basename='visualization')
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'projects', ProjectAnalyticsView, basename='project-analytics')

urlpatterns = [
    path('', include(router.urls)),
]