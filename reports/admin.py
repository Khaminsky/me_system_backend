from django.contrib import admin
from .models import ReportTemplate, GeneratedReport, ReportSchedule


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'is_active', 'created_at')
    list_filter = ('report_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'report_type')
        }),
        ('Configuration', {
            'fields': ('template_config',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'template', 'survey', 'status', 'export_format', 'generated_at')
    list_filter = ('status', 'export_format', 'generated_at')
    search_fields = ('title', 'survey__name', 'template__name')
    readonly_fields = ('generated_at', 'completed_at')
    fieldsets = (
        ('Reference', {
            'fields': ('template', 'survey')
        }),
        ('Report Details', {
            'fields': ('title', 'export_format')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Content', {
            'fields': ('content', 'file_path'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('generated_by', 'generated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ('template', 'survey', 'frequency', 'is_active', 'last_generated', 'next_scheduled')
    list_filter = ('frequency', 'is_active', 'created_at')
    search_fields = ('template__name', 'survey__name')
    readonly_fields = ('created_at', 'last_generated')
    fieldsets = (
        ('Reference', {
            'fields': ('template', 'survey')
        }),
        ('Schedule', {
            'fields': ('frequency', 'is_active')
        }),
        ('Tracking', {
            'fields': ('last_generated', 'next_scheduled')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
