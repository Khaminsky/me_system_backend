from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings


class SystemSettings(models.Model):
    """
    Singleton model for global system settings.
    Only one instance should exist in the database.
    """

    # Branding Settings
    app_name = models.CharField(
        max_length=100,
        default='M&E Data Intelligence System',
        help_text='Application name displayed throughout the system'
    )
    company_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Company or organization name'
    )
    logo = models.ImageField(
        upload_to='branding/logos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg', 'svg'])],
        help_text='Company logo (PNG, JPG, or SVG)'
    )
    favicon = models.ImageField(
        upload_to='branding/favicons/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['ico', 'png'])],
        help_text='Browser favicon (ICO or PNG)'
    )

    # Theme Settings
    primary_color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text='Primary theme color (hex format, e.g., #3B82F6)'
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#10B981',
        help_text='Secondary theme color (hex format)'
    )
    accent_color = models.CharField(
        max_length=7,
        default='#F59E0B',
        help_text='Accent color for highlights (hex format)'
    )
    sidebar_color = models.CharField(
        max_length=7,
        default='#1F2937',
        help_text='Sidebar background color (hex format)'
    )

    # Localization Settings
    TIMEZONE_CHOICES = [
        ('UTC', 'UTC'),
        ('Africa/Nairobi', 'East Africa Time (EAT)'),
        ('Africa/Lagos', 'West Africa Time (WAT)'),
        ('Africa/Johannesburg', 'South Africa Time (SAST)'),
        ('Africa/Cairo', 'Egypt Time (EET)'),
        ('America/New_York', 'Eastern Time (ET)'),
        ('America/Chicago', 'Central Time (CT)'),
        ('America/Los_Angeles', 'Pacific Time (PT)'),
        ('Europe/London', 'Greenwich Mean Time (GMT)'),
        ('Europe/Paris', 'Central European Time (CET)'),
        ('Asia/Dubai', 'Gulf Standard Time (GST)'),
        ('Asia/Kolkata', 'India Standard Time (IST)'),
        ('Asia/Shanghai', 'China Standard Time (CST)'),
        ('Asia/Tokyo', 'Japan Standard Time (JST)'),
    ]

    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='UTC',
        help_text='Default timezone for the system'
    )

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'French'),
        ('es', 'Spanish'),
        ('pt', 'Portuguese'),
        ('ar', 'Arabic'),
        ('sw', 'Swahili'),
    ]

    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text='Default system language'
    )

    date_format = models.CharField(
        max_length=20,
        default='YYYY-MM-DD',
        help_text='Date format (e.g., YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY)'
    )

    # System Preferences
    items_per_page = models.IntegerField(
        default=10,
        help_text='Default number of items per page in lists'
    )

    enable_email_notifications = models.BooleanField(
        default=True,
        help_text='Enable email notifications system-wide'
    )

    enable_data_export = models.BooleanField(
        default=True,
        help_text='Allow users to export data'
    )

    max_file_upload_size_mb = models.IntegerField(
        default=50,
        help_text='Maximum file upload size in megabytes'
    )

    # Contact Information
    support_email = models.EmailField(
        blank=True,
        help_text='Support email address'
    )
    support_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Support phone number'
    )

    # Footer Settings
    footer_text = models.CharField(
        max_length=200,
        blank=True,
        help_text='Custom footer text'
    )

    show_powered_by = models.BooleanField(
        default=True,
        help_text='Show "Powered by" text in footer'
    )

    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='settings_updates'
    )

    class Meta:
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    def save(self, *args, **kwargs):
        """
        Ensure only one instance exists (singleton pattern)
        """
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Prevent deletion of settings
        """
        pass

    @classmethod
    def load(cls):
        """
        Load the singleton instance, creating it if it doesn't exist
        """
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"System Settings - {self.app_name}"
