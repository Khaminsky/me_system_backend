from django.contrib import admin
from .models import Indicator, IndicatorValue, IndicatorTarget


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'indicator_type', 'unit', 'baseline', 'target', 'is_active', 'created_at')
    list_filter = ('indicator_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'indicator_type', 'unit')
        }),
        ('Targets', {
            'fields': ('baseline', 'target')
        }),
        ('Formula', {
            'fields': ('formula',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(IndicatorValue)
class IndicatorValueAdmin(admin.ModelAdmin):
    list_display = ('indicator', 'survey', 'value', 'period', 'calculated_at')
    list_filter = ('period', 'calculated_at', 'indicator')
    search_fields = ('indicator__name', 'survey__name', 'period')
    readonly_fields = ('calculated_at',)
    fieldsets = (
        ('Reference', {
            'fields': ('indicator', 'survey')
        }),
        ('Value', {
            'fields': ('value', 'period')
        }),
        ('Details', {
            'fields': ('notes', 'calculated_by', 'calculated_at')
        }),
    )


@admin.register(IndicatorTarget)
class IndicatorTargetAdmin(admin.ModelAdmin):
    list_display = ('indicator', 'period', 'target_value', 'achieved_value', 'status', 'set_at')
    list_filter = ('status', 'period', 'set_at')
    search_fields = ('indicator__name', 'period')
    readonly_fields = ('set_at', 'updated_at')
    fieldsets = (
        ('Reference', {
            'fields': ('indicator', 'period')
        }),
        ('Values', {
            'fields': ('target_value', 'achieved_value')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Metadata', {
            'fields': ('set_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
