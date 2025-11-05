from django.db import models
from django.conf import settings
from surveys.models import Survey, SurveyData


class ValidationRule(models.Model):
    """Define validation rules for survey data"""
    RULE_TYPES = [
        ('required', 'Required Field'),
        ('numeric', 'Numeric Value'),
        ('date', 'Date Format'),
        ('email', 'Email Format'),
        ('range', 'Value Range'),
        ('pattern', 'Regex Pattern'),
        ('unique', 'Unique Value'),
        ('choice', 'Choice from List'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    field_name = models.CharField(max_length=255)
    parameters = models.JSONField(default=dict, help_text="Rule-specific parameters (e.g., min, max, pattern)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.name} ({self.rule_type})"

    class Meta:
        ordering = ['-created_at']


class CleaningTask(models.Model):
    """Track data cleaning operations"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='cleaning_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_records = models.IntegerField(default=0)
    cleaned_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    error_log = models.JSONField(default=list, help_text="List of errors encountered")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Cleaning Task for {self.survey.name} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class DataQualityReport(models.Model):
    """Store data quality assessment results"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='quality_reports')
    total_records = models.IntegerField()
    valid_records = models.IntegerField()
    invalid_records = models.IntegerField()
    completeness_score = models.FloatField(help_text="Percentage of non-null values")
    accuracy_score = models.FloatField(help_text="Percentage of valid values")
    consistency_score = models.FloatField(help_text="Percentage of consistent values")
    overall_quality_score = models.FloatField()
    issues = models.JSONField(default=list, help_text="List of identified data quality issues")
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Quality Report for {self.survey.name}"

    class Meta:
        ordering = ['-generated_at']
