from rest_framework import serializers
from .models import ValidationRule, CleaningTask, DataQualityReport


class ValidationRuleSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ValidationRule
        fields = [
            'id', 'name', 'description', 'rule_type', 'field_name',
            'parameters', 'is_active', 'created_at', 'updated_at',
            'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'created_by_username']


class CleaningTaskSerializer(serializers.ModelSerializer):
    survey_name = serializers.CharField(source='survey.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = CleaningTask
        fields = [
            'id', 'survey', 'survey_name', 'status', 'started_at',
            'completed_at', 'total_records', 'cleaned_records',
            'failed_records', 'error_log', 'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'survey_name', 'created_by', 'created_by_username']


class DataQualityReportSerializer(serializers.ModelSerializer):
    survey_name = serializers.CharField(source='survey.name', read_only=True)
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = DataQualityReport
        fields = [
            'id', 'survey', 'survey_name', 'total_records', 'valid_records',
            'invalid_records', 'completeness_score', 'accuracy_score',
            'consistency_score', 'overall_quality_score', 'issues',
            'generated_at', 'generated_by', 'generated_by_username'
        ]
        read_only_fields = ['id', 'survey_name', 'generated_at', 'generated_by', 'generated_by_username']

