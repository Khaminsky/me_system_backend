from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ValidationRuleViewSet, CleaningTaskViewSet, DataQualityReportViewSet, DataValidationView

router = DefaultRouter()
router.register(r'validation-rules', ValidationRuleViewSet, basename='validation-rule')
router.register(r'cleaning-tasks', CleaningTaskViewSet, basename='cleaning-task')
router.register(r'quality-reports', DataQualityReportViewSet, basename='quality-report')

urlpatterns = [
    path('', include(router.urls)),
    path('validate/<int:survey_id>/', DataValidationView.as_view(), name='validate-survey'),
]

