from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    archived_by_username = serializers.CharField(source='archived_by.username', read_only=True, allow_null=True)
    survey_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'description',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
            'is_archived',
            'archived_date',
            'archived_by',
            'archived_by_username',
            'survey_count',
        ]
        read_only_fields = [
            'id',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
            'is_archived',
            'archived_date',
            'archived_by',
            'archived_by_username',
            'survey_count',
        ]

    def get_survey_count(self, obj):
        return obj.surveys.filter(is_archived=False).count()

