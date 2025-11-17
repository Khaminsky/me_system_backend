from django.contrib import admin
from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for System Settings
    """
    fieldsets = (
        ('Branding', {
            'fields': ('app_name', 'company_name', 'logo', 'favicon')
        }),
        ('Theme Colors', {
            'fields': ('primary_color', 'secondary_color', 'accent_color', 'sidebar_color')
        }),
        ('Localization', {
            'fields': ('timezone', 'language', 'date_format')
        }),
        ('System Preferences', {
            'fields': ('items_per_page', 'enable_email_notifications', 'enable_data_export', 'max_file_upload_size_mb')
        }),
        ('Contact Information', {
            'fields': ('support_email', 'support_phone')
        }),
        ('Footer', {
            'fields': ('footer_text', 'show_powered_by')
        }),
        ('Metadata', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('updated_at', 'updated_by')

    def has_add_permission(self, request):
        """Prevent adding new instances (singleton)"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion"""
        return False

    def save_model(self, request, obj, form, change):
        """Set updated_by when saving"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
