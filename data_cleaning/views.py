from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import pandas as pd
from .models import ValidationRule, CleaningTask, DataQualityReport
from .serializers import ValidationRuleSerializer, CleaningTaskSerializer, DataQualityReportSerializer
from .services import DataCleaningService
from surveys.models import Survey, SurveyData
from users.permissions import CanValidateData, CanViewReports


class ValidationRuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing validation rules.
    """
    queryset = ValidationRule.objects.all()
    serializer_class = ValidationRuleSerializer
    permission_classes = [IsAuthenticated, CanValidateData]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        operation_description="List all validation rules",
        operation_summary="Get validation rules"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CleaningTaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing data cleaning tasks.
    """
    queryset = CleaningTask.objects.all()
    serializer_class = CleaningTaskSerializer
    permission_classes = [IsAuthenticated, CanValidateData]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        operation_description="Get cleaning tasks for a specific survey",
        operation_summary="List cleaning tasks by survey"
    )
    @action(detail=False, methods=['get'])
    def by_survey(self, request):
        survey_id = request.query_params.get('survey_id')
        if not survey_id:
            return Response({'error': 'survey_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        tasks = CleaningTask.objects.filter(survey_id=survey_id)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class DataQualityReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for data quality reports.
    """
    queryset = DataQualityReport.objects.all()
    serializer_class = DataQualityReportSerializer
    permission_classes = [IsAuthenticated, CanViewReports]

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)

    @swagger_auto_schema(
        operation_description="Get quality reports for a specific survey",
        operation_summary="List quality reports by survey"
    )
    @action(detail=False, methods=['get'])
    def by_survey(self, request):
        survey_id = request.query_params.get('survey_id')
        if not survey_id:
            return Response({'error': 'survey_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        reports = DataQualityReport.objects.filter(survey_id=survey_id)
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)


class DataValidationView(APIView):
    """
    API endpoint for validating survey data.
    Loads survey data and generates a comprehensive quality report.
    """
    permission_classes = [IsAuthenticated, CanValidateData]

    @swagger_auto_schema(
        operation_description="Validate survey data and generate quality report",
        operation_summary="Validate survey data",
        responses={
            200: openapi.Response('Validation report generated successfully'),
            404: openapi.Response('Survey not found'),
            400: openapi.Response('Error processing survey data')
        }
    )
    def get(self, request, survey_id):
        """
        Validate survey data by loading it into a DataFrame and running quality checks.
        """
        try:
            # Get the survey
            survey = Survey.objects.get(id=survey_id)

            # Load survey data
            survey_data = SurveyData.objects.filter(survey=survey).values('data')

            if not survey_data.exists():
                return Response(
                    {'error': 'No data found for this survey'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Convert to DataFrame
            data_list = [item['data'] for item in survey_data]
            df = pd.DataFrame(data_list)

            # Run cleaning service
            cleaning_service = DataCleaningService(df)
            report = cleaning_service.generate_quality_report()

            return Response(report, status=status.HTTP_200_OK)

        except Survey.DoesNotExist:
            return Response(
                {'error': 'Survey not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error processing survey data: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
