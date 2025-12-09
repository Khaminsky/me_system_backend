from django.db import models
from django.conf import settings
from surveys.models import Survey
from projects.models import Project


class Indicator(models.Model):
    """Define M&E indicators"""
    INDICATOR_TYPES = [
        ('input', 'Input'),
        ('output', 'Output'),
        ('outcome', 'Outcome'),
        ('impact', 'Impact'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='indicators', null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    indicator_type = models.CharField(max_length=20, choices=INDICATOR_TYPES)
    unit = models.CharField(max_length=100, help_text="Unit of measurement (e.g., %, count, ratio)")
    baseline = models.FloatField(null=True, blank=True)
    target = models.FloatField(null=True, blank=True)
    formula = models.TextField(help_text="Formula for calculation (e.g., field1 + field2)")
    filter_criteria = models.JSONField(
        default=dict,
        blank=True,
        help_text="Filter criteria as JSON (e.g., {'region': 'North', 'status': 'Active'})"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.name} ({self.indicator_type})"

    class Meta:
        ordering = ['-created_at']


class IndicatorValue(models.Model):
    """Store calculated indicator values"""
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name='values')
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='indicator_values')
    value = models.FloatField()
    period = models.CharField(max_length=50, help_text="Time period (e.g., Q1 2024, Jan 2024)")
    calculated_at = models.DateTimeField(auto_now_add=True)
    calculated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.indicator.name} - {self.period}: {self.value}"

    class Meta:
        ordering = ['-calculated_at']
        unique_together = ['indicator', 'survey', 'period']


class IndicatorTarget(models.Model):
    """Track indicator targets and progress"""
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name='targets')
    period = models.CharField(max_length=50)
    target_value = models.FloatField()
    achieved_value = models.FloatField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('on_track', 'On Track'), ('at_risk', 'At Risk'), ('off_track', 'Off Track')],
        default='on_track'
    )
    set_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.indicator.name} - {self.period}"

    class Meta:
        ordering = ['-set_at']
        unique_together = ['indicator', 'period']
