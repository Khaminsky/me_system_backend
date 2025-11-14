from django.db import models
from django.conf import settings

# Create your models here.
class Survey(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='uploads/')
    total_records = models.IntegerField(default=0)
    cleaned_records = models.IntegerField(default=0)
    cleaned_file = models.FileField(upload_to='cleaned_uploads/', blank=True, null=True)
    cleaned = models.BooleanField(default=False)
    cleaned_date = models.DateTimeField(null=True, blank=True)
    cleaned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='cleaned_by', blank=True)
    is_archived = models.BooleanField(default=False)
    archived_date = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='archived_surveys', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-upload_date']

class SurveyData(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    data = models.JSONField()
    sheet_name = models.CharField(max_length=255, blank=True, null=True, help_text="Name of the Excel sheet this data came from")
    created_at = models.DateTimeField(auto_now_add=True)
    cleaned_data = models.JSONField(null=True, blank=True)
    cleaned = models.BooleanField(default=False)
    cleaned_date = models.DateTimeField(null=True, blank=True)
    cleaned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='cleaned_data_by', blank=True)

    def __str__(self):
        return f"Data for {self.survey.name}"

    class Meta:
        ordering = ['-id']