from django.contrib import admin
from .models import ValidationRule, CleaningTask, DataQualityReport


@admin.register(ValidationRule)
class ValidationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'field_name', 'is_active', 'created_at')
    list_filter = ('rule_type', 'is_active', 'created_at')
    search_fields = ('name', 'field_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'rule_type', 'field_name')
        }),
        ('Configuration', {
            'fields': ('parameters', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CleaningTask)
class CleaningTaskAdmin(admin.ModelAdmin):
    list_display = ('survey', 'status', 'total_records', 'cleaned_records', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('survey__name',)
    readonly_fields = ('created_at', 'started_at', 'completed_at')
    fieldsets = (
        ('Task Information', {
            'fields': ('survey', 'status')
        }),
        ('Progress', {
            'fields': ('total_records', 'cleaned_records', 'failed_records')
        }),
        ('Timing', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
        ('Details', {
            'fields': ('error_log', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DataQualityReport)
class DataQualityReportAdmin(admin.ModelAdmin):
    list_display = ('survey', 'overall_quality_score', 'valid_records', 'invalid_records', 'generated_at')
    list_filter = ('generated_at',)
    search_fields = ('survey__name',)
    readonly_fields = ('generated_at',)
    fieldsets = (
        ('Report Information', {
            'fields': ('survey', 'generated_by')
        }),
        ('Records', {
            'fields': ('total_records', 'valid_records', 'invalid_records')
        }),
        ('Quality Scores', {
            'fields': ('completeness_score', 'accuracy_score', 'consistency_score', 'overall_quality_score')
        }),
        ('Issues', {
            'fields': ('issues',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )
