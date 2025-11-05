from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportTemplateViewSet, GeneratedReportViewSet, ReportScheduleViewSet, ReportSummaryView, ReportExportView

router = DefaultRouter()
router.register(r'templates', ReportTemplateViewSet, basename='report-template')
router.register(r'generated', GeneratedReportViewSet, basename='generated-report')
router.register(r'schedules', ReportScheduleViewSet, basename='report-schedule')

urlpatterns = [
    path('', include(router.urls)),
    path('summary/<int:survey_id>/', ReportSummaryView.as_view(), name='report-summary'),
    path('export/<int:survey_id>/', ReportExportView.as_view(), name='report-export'),
]

