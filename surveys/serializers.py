from rest_framework import serializers
from .models import Survey, SurveyData

class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = '__all__'

class SurveyDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyData
        fields = '__all__'
