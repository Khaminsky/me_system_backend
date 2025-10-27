from django.shortcuts import render
from pandas import read_excel
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from surveys.models import Survey, SurveyData
from .serializers import SurveySerializer

# Create your views here.
class SurveyUploadView(APIView):
    def post(self, request):
        file_obj = request.FILES['file']
        if not file_obj.name.endswith('.csv'):
            return Response({'error': 'File must be a CSV'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        name = request.data.get('name', file_obj.name)
        description = request.data.get('description', '')

        survey = Survey.objects.create(
            name=name,
            description=description,
            uploaded_by=request.user,
            file=file_obj
        )
        
        try: 
            df = read_excel(file_obj)
            for _, row in df.iterrows():
                SurveyData.objects.create(
                    survey=survey,
                    data=row.to_dict()
                )
                survey.total_records = len(df)
                survey.save()
                serializer = SurveySerializer(survey)
                return Response({"message": "Upload successful", "records": survey.total_records}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({'error': 'Error reading file'}, status=status.HTTP_400_BAD_REQUEST)
        
class SurveyListView(APIView):
    def get(self, request):
        surveys = Survey.objects.all()
        serializer = SurveySerializer(surveys, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)