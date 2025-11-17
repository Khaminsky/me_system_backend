from rest_framework import serializers
from .models import SystemSettings


class SystemSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for System Settings with all configuration options
    """
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    logo_url = serializers.SerializerMethodField()
    favicon_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemSettings
        fields = [
            'id',
            # Branding
            'app_name',
            'company_name',
            'logo',
            'logo_url',
            'favicon',
            'favicon_url',
            # Theme
            'primary_color',
            'secondary_color',
            'accent_color',
            'sidebar_color',
            # Localization
            'timezone',
            'language',
            'date_format',
            # System Preferences
            'items_per_page',
            'enable_email_notifications',
            'enable_data_export',
            'max_file_upload_size_mb',
            # Contact
            'support_email',
            'support_phone',
            # Footer
            'footer_text',
            'show_powered_by',
            # Metadata
            'updated_at',
            'updated_by',
            'updated_by_username',
        ]
        read_only_fields = [
            'id',
            'updated_at',
            'updated_by',
            'updated_by_username',
            'logo_url',
            'favicon_url',
        ]
    
    def get_logo_url(self, obj):
        """Return full URL for logo if it exists"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def get_favicon_url(self, obj):
        """Return full URL for favicon if it exists"""
        if obj.favicon:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.favicon.url)
            return obj.favicon.url
        return None
    
    def update(self, instance, validated_data):
        """Override update to set updated_by"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)


class SystemSettingsPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer for System Settings (no sensitive data)
    Used for unauthenticated requests
    """
    logo_url = serializers.SerializerMethodField()
    favicon_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemSettings
        fields = [
            'app_name',
            'company_name',
            'logo_url',
            'favicon_url',
            'primary_color',
            'secondary_color',
            'accent_color',
            'sidebar_color',
            'timezone',
            'language',
            'date_format',
            'footer_text',
            'show_powered_by',
        ]
    
    def get_logo_url(self, obj):
        """Return full URL for logo if it exists"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def get_favicon_url(self, obj):
        """Return full URL for favicon if it exists"""
        if obj.favicon:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.favicon.url)
            return obj.favicon.url
        return None

