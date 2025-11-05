from rest_framework import serializers
from .models import Survey, SurveyData

class SurveySerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    cleaned_by_username = serializers.CharField(source='cleaned_by.username', read_only=True, allow_null=True)
    archived_by_username = serializers.CharField(source='archived_by.username', read_only=True, allow_null=True)

    class Meta:
        model = Survey
        fields = [
            'id',
            'name',
            'description',
            'uploaded_by',
            'uploaded_by_username',
            'upload_date',
            'file',
            'total_records',
            'cleaned_records',
            'cleaned_file',
            'cleaned',
            'cleaned_date',
            'cleaned_by',
            'cleaned_by_username',
            'is_archived',
            'archived_date',
            'archived_by',
            'archived_by_username',
        ]
        read_only_fields = [
            'id',
            'uploaded_by',
            'uploaded_by_username',
            'upload_date',
            'total_records',
            'cleaned_records',
            'cleaned_file',
            'cleaned',
            'cleaned_date',
            'cleaned_by',
            'cleaned_by_username',
            'is_archived',
            'archived_date',
            'archived_by',
            'archived_by_username',
        ]

class SurveyDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyData
        fields = '__all__'
