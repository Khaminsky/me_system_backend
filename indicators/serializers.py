from rest_framework import serializers
from .models import Indicator, IndicatorValue, IndicatorTarget


class IndicatorSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Indicator
        fields = [
            'id', 'project', 'project_name', 'name', 'description', 'indicator_type', 'unit',
            'baseline', 'target', 'formula', 'is_active', 'filter_criteria',
            'created_at', 'updated_at', 'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'project_name', 'created_at', 'updated_at', 'created_by', 'created_by_username']


class IndicatorValueSerializer(serializers.ModelSerializer):
    indicator_name = serializers.CharField(source='indicator.name', read_only=True)
    survey_name = serializers.CharField(source='survey.name', read_only=True)
    calculated_by_username = serializers.CharField(source='calculated_by.username', read_only=True)
    
    class Meta:
        model = IndicatorValue
        fields = [
            'id', 'indicator', 'indicator_name', 'survey', 'survey_name',
            'value', 'period', 'calculated_at', 'calculated_by',
            'calculated_by_username', 'notes'
        ]
        read_only_fields = ['id', 'indicator_name', 'survey_name', 'calculated_at', 'calculated_by', 'calculated_by_username']


class IndicatorTargetSerializer(serializers.ModelSerializer):
    indicator_name = serializers.CharField(source='indicator.name', read_only=True)
    
    class Meta:
        model = IndicatorTarget
        fields = [
            'id', 'indicator', 'indicator_name', 'period', 'target_value',
            'achieved_value', 'status', 'set_at', 'updated_at'
        ]
        read_only_fields = ['id', 'indicator_name', 'set_at', 'updated_at']

