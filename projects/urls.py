from django.urls import path
from .views import (
    ProjectListView,
    ProjectDetailView,
    ProjectArchivedListView,
    ProjectRestoreView,
    ProjectSurveysView
)

urlpatterns = [
    path('', ProjectListView.as_view(), name='project-list'),
    path('<int:project_id>/', ProjectDetailView.as_view(), name='project-detail'),
    path('archived/', ProjectArchivedListView.as_view(), name='project-archived-list'),
    path('<int:project_id>/restore/', ProjectRestoreView.as_view(), name='project-restore'),
    path('<int:project_id>/surveys/', ProjectSurveysView.as_view(), name='project-surveys'),
]

