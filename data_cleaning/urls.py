from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ValidationRuleViewSet,
    CleaningTaskViewSet,
    DataQualityReportViewSet,
    DataValidationView,
    SurveyDataPreviewView,
    SurveyDataCleaningView
)

router = DefaultRouter()
router.register(r'validation-rules', ValidationRuleViewSet, basename='validation-rule')
router.register(r'cleaning-tasks', CleaningTaskViewSet, basename='cleaning-task')
router.register(r'quality-reports', DataQualityReportViewSet, basename='quality-report')

urlpatterns = [
    path('', include(router.urls)),
    path('validate/<int:survey_id>/', DataValidationView.as_view(), name='validate-survey'),
    path('preview/<int:survey_id>/', SurveyDataPreviewView.as_view(), name='preview-survey'),
    path('clean/<int:survey_id>/remove-columns/', SurveyDataCleaningView.as_view({'post': 'remove_columns'}), name='remove-columns'),
    path('clean/<int:survey_id>/add-column/', SurveyDataCleaningView.as_view({'post': 'add_column'}), name='add-column'),
    path('clean/<int:survey_id>/rename-column/', SurveyDataCleaningView.as_view({'post': 'rename_column'}), name='rename-column'),
    path('clean/<int:survey_id>/remove-duplicates/', SurveyDataCleaningView.as_view({'post': 'remove_duplicates'}), name='remove-duplicates'),
    path('clean/<int:survey_id>/handle-missing/', SurveyDataCleaningView.as_view({'post': 'handle_missing'}), name='handle-missing'),
    path('clean/<int:survey_id>/find-replace/', SurveyDataCleaningView.as_view({'post': 'find_replace'}), name='find-replace'),
    path('clean/<int:survey_id>/standardize/', SurveyDataCleaningView.as_view({'post': 'standardize'}), name='standardize'),
    path('clean/<int:survey_id>/create-variable/', SurveyDataCleaningView.as_view({'post': 'create_variable'}), name='create-variable'),
    path('clean/<int:survey_id>/save-cleaned/', SurveyDataCleaningView.as_view({'post': 'save_cleaned'}), name='save-cleaned'),
]

