from rest_framework import serializers
from .models import ReportTemplate, GeneratedReport, ReportSchedule


class ReportTemplateSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'report_type', 'template_config',
            'is_active', 'created_at', 'updated_at', 'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'created_by_username']


class GeneratedReportSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    survey_name = serializers.CharField(source='survey.name', read_only=True)
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = GeneratedReport
        fields = [
            'id', 'template', 'template_name', 'survey', 'survey_name',
            'title', 'status', 'export_format', 'content', 'file_path',
            'generated_at', 'completed_at', 'generated_by', 'generated_by_username'
        ]
        read_only_fields = ['id', 'template_name', 'survey_name', 'generated_at', 'completed_at', 'generated_by', 'generated_by_username']


class ReportScheduleSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    survey_name = serializers.CharField(source='survey.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'template', 'template_name', 'survey', 'survey_name',
            'frequency', 'is_active', 'last_generated', 'next_scheduled',
            'created_at', 'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'template_name', 'survey_name', 'created_at', 'created_by', 'created_by_username']

