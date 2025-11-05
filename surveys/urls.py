from django.urls import path
from .views import (
    SurveyUploadView,
    SurveyListView,
    SurveyDetailView,
    SurveyArchivedListView,
    SurveyRestoreView
)

urlpatterns = [
    path('upload/', SurveyUploadView.as_view(), name='survey-upload'),
    path('', SurveyListView.as_view(), name='survey-list'),
    path('<int:survey_id>/', SurveyDetailView.as_view(), name='survey-detail'),
    path('archived/', SurveyArchivedListView.as_view(), name='survey-archived-list'),
    path('<int:survey_id>/restore/', SurveyRestoreView.as_view(), name='survey-restore'),
]
