from django.db import models
from django.conf import settings
from surveys.models import Survey


class ReportTemplate(models.Model):
    """Define report templates"""
    REPORT_TYPES = [
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('dashboard', 'Dashboard'),
        ('export', 'Export Report'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    template_config = models.JSONField(default=dict, help_text="Template configuration (sections, fields, etc.)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.name} ({self.report_type})"

    class Meta:
        ordering = ['-created_at']


class GeneratedReport(models.Model):
    """Store generated reports"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]

    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='generated_reports')
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    export_format = models.CharField(max_length=20, choices=EXPORT_FORMATS, default='pdf')
    content = models.JSONField(default=dict, help_text="Report content/data")
    file_path = models.FileField(upload_to='reports/', null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.title} - {self.status}"

    class Meta:
        ordering = ['-generated_at']


class ReportSchedule(models.Model):
    """Schedule automatic report generation"""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='schedules')
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='report_schedules')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)
    last_generated = models.DateTimeField(null=True, blank=True)
    next_scheduled = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.template.name} - {self.frequency}"

    class Meta:
        ordering = ['-created_at']
