# analytics/serializers.py

from rest_framework import serializers
from .models import Visualization, Dashboard, DashboardItem, DataDimension

class VisualizationSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Visualization
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class DashboardItemSerializer(serializers.ModelSerializer):
    visualization_name = serializers.CharField(source='visualization.name', read_only=True)
    visualization_type = serializers.CharField(source='visualization.visualization_type', read_only=True)
    
    class Meta:
        model = DashboardItem
        fields = '__all__'


class DashboardSerializer(serializers.ModelSerializer):
    items = DashboardItemSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = Dashboard
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class DataDimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDimension
        fields = '__all__'