from django.urls import path
from .views import (
    SurveyUploadView,
    SurveyListView,
    SurveyDetailView,
    SurveyArchivedListView,
    SurveyRestoreView,
    SurveyFieldsView,
    SurveyProcessSheetView
)

urlpatterns = [
    path('upload/', SurveyUploadView.as_view(), name='survey-upload'),
    path('', SurveyListView.as_view(), name='survey-list'),
    path('<int:survey_id>/', SurveyDetailView.as_view(), name='survey-detail'),
    path('<int:survey_id>/fields/', SurveyFieldsView.as_view(), name='survey-fields'),
    path('<int:survey_id>/process-sheet/', SurveyProcessSheetView.as_view(), name='survey-process-sheet'),
    path('archived/', SurveyArchivedListView.as_view(), name='survey-archived-list'),
    path('<int:survey_id>/restore/', SurveyRestoreView.as_view(), name='survey-restore'),
]
