from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import FileResponse
import pandas as pd
from .models import ReportTemplate, GeneratedReport, ReportSchedule
from .serializers import ReportTemplateSerializer, GeneratedReportSerializer, ReportScheduleSerializer
from .services import ReportGenerationService
from surveys.models import Survey, SurveyData
from users.permissions import CanGenerateReports, CanViewReports


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing report templates.
    """
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsAuthenticated, CanGenerateReports]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        operation_description="List all report templates",
        operation_summary="Get report templates"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class GeneratedReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for generated reports.
    """
    queryset = GeneratedReport.objects.all()
    serializer_class = GeneratedReportSerializer
    permission_classes = [IsAuthenticated, CanViewReports]

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)

    @swagger_auto_schema(
        operation_description="Get reports for a specific survey",
        operation_summary="List reports by survey"
    )
    @action(detail=False, methods=['get'])
    def by_survey(self, request):
        survey_id = request.query_params.get('survey_id')
        if not survey_id:
            return Response({'error': 'survey_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        reports = GeneratedReport.objects.filter(survey_id=survey_id)
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)


class ReportScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for report schedules.
    """
    queryset = ReportSchedule.objects.all()
    serializer_class = ReportScheduleSerializer
    permission_classes = [IsAuthenticated, CanGenerateReports]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        operation_description="Get schedules for a specific survey",
        operation_summary="List schedules by survey"
    )
    @action(detail=False, methods=['get'])
    def by_survey(self, request):
        survey_id = request.query_params.get('survey_id')
        if not survey_id:
            return Response({'error': 'survey_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        schedules = ReportSchedule.objects.filter(survey_id=survey_id)
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)


class ReportSummaryView(APIView):
    """
    API endpoint for generating survey summary reports.
    """
    permission_classes = [IsAuthenticated, CanViewReports]

    @swagger_auto_schema(
        operation_description="Generate a summary report for a survey",
        operation_summary="Get survey summary",
        responses={
            200: openapi.Response('Summary report generated successfully'),
            404: openapi.Response('Survey not found'),
            400: openapi.Response('Error generating summary')
        }
    )
    def get(self, request, survey_id):
        """
        Generate a summary report with key statistics.
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

            # Generate summary
            report_service = ReportGenerationService(df, survey.name)
            summary = report_service.generate_summary()

            return Response(summary, status=status.HTTP_200_OK)

        except Survey.DoesNotExist:
            return Response(
                {'error': 'Survey not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error generating summary: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ReportExportView(APIView):
    """
    API endpoint for exporting survey data.
    """
    permission_classes = [IsAuthenticated, CanViewReports]

    @swagger_auto_schema(
        operation_description="Export survey data in specified format",
        operation_summary="Export survey data",
        manual_parameters=[
            openapi.Parameter(
                'format',
                openapi.IN_QUERY,
                description='Export format (csv, excel, json)',
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response('File exported successfully'),
            404: openapi.Response('Survey not found'),
            400: openapi.Response('Invalid format or error exporting')
        }
    )
    def get(self, request, survey_id):
        """
        Export survey data in the specified format.
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

            # Get export format
            export_format = request.query_params.get('format', 'csv').lower()

            # Generate export
            report_service = ReportGenerationService(df, survey.name)

            if export_format == 'csv':
                file_obj, filename = report_service.export_to_csv()
                response = FileResponse(file_obj, content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response

            elif export_format == 'excel':
                file_obj, filename = report_service.export_to_excel()
                response = FileResponse(
                    file_obj,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response

            elif export_format == 'json':
                json_data, filename = report_service.export_to_json()
                response = FileResponse(
                    iter([json_data.encode()]),
                    content_type='application/json'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response

            else:
                return Response(
                    {'error': f'Unsupported format: {export_format}. Use csv, excel, or json'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Survey.DoesNotExist:
            return Response(
                {'error': 'Survey not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error exporting data: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
