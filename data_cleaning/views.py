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


class SurveyDataPreviewView(APIView):
    """
    API endpoint for previewing survey data with pagination.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get paginated preview of survey data",
        operation_summary="Preview survey data",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response('Data preview retrieved successfully'),
            404: openapi.Response('Survey not found')
        }
    )
    def get(self, request, survey_id):
        """
        Get paginated preview of survey data.
        """
        try:
            survey = Survey.objects.get(id=survey_id)
            survey_data = SurveyData.objects.filter(survey=survey).values('data')

            if not survey_data.exists():
                return Response(
                    {'error': 'No data found for this survey'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Convert to DataFrame
            data_list = [item['data'] for item in survey_data]
            df = pd.DataFrame(data_list)

            # Get pagination parameters
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 50))

            # Get preview data
            cleaning_service = DataCleaningService(df)
            preview = cleaning_service.get_preview_data(page=page, page_size=page_size)

            return Response(preview, status=status.HTTP_200_OK)

        except Survey.DoesNotExist:
            return Response(
                {'error': 'Survey not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error retrieving data: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class SurveyDataCleaningView(viewsets.ViewSet):
    """
    API endpoint for performing various data cleaning operations on survey data.
    """
    permission_classes = [IsAuthenticated]

    def _get_dataframe(self, survey_id):
        """Helper method to get DataFrame from survey."""
        survey = Survey.objects.get(id=survey_id)
        survey_data = SurveyData.objects.filter(survey=survey).values('data')

        if not survey_data.exists():
            raise ValueError('No data found for this survey')

        data_list = [item['data'] for item in survey_data]
        return pd.DataFrame(data_list), survey

    @swagger_auto_schema(
        operation_description="Remove columns from survey data",
        operation_summary="Remove columns",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'columns': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            }
        )
    )
    def remove_columns(self, request, survey_id=None):
        """Remove specified columns from survey data."""
        try:
            df, survey = self._get_dataframe(survey_id)
            columns = request.data.get('columns', [])

            cleaning_service = DataCleaningService(df)
            df_modified, report = cleaning_service.remove_columns(columns)

            # Return preview of modified data
            preview_service = DataCleaningService(df_modified)
            preview = preview_service.get_preview_data(page=1, page_size=50)

            return Response({
                'report': report,
                'preview': preview
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Add a new column to survey data",
        operation_summary="Add column",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'column_name': openapi.Schema(type=openapi.TYPE_STRING),
                'default_value': openapi.Schema(type=openapi.TYPE_STRING),
            }
        )
    )
    def add_column(self, request, survey_id=None):
        """Add a new column to survey data."""
        try:
            df, survey = self._get_dataframe(survey_id)
            column_name = request.data.get('column_name')
            default_value = request.data.get('default_value')

            cleaning_service = DataCleaningService(df)
            df_modified, report = cleaning_service.add_column(column_name, default_value)

            preview_service = DataCleaningService(df_modified)
            preview = preview_service.get_preview_data(page=1, page_size=50)

            return Response({
                'report': report,
                'preview': preview
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Rename a column in survey data",
        operation_summary="Rename column",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'old_name': openapi.Schema(type=openapi.TYPE_STRING),
                'new_name': openapi.Schema(type=openapi.TYPE_STRING),
            }
        )
    )
    def rename_column(self, request, survey_id=None):
        """Rename a column in survey data."""
        try:
            df, survey = self._get_dataframe(survey_id)
            old_name = request.data.get('old_name')
            new_name = request.data.get('new_name')

            cleaning_service = DataCleaningService(df)
            df_modified, report = cleaning_service.rename_column(old_name, new_name)

            preview_service = DataCleaningService(df_modified)
            preview = preview_service.get_preview_data(page=1, page_size=50)

            return Response({
                'report': report,
                'preview': preview
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Remove duplicate rows from survey data",
        operation_summary="Remove duplicates",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'subset': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                'keep': openapi.Schema(type=openapi.TYPE_STRING, enum=['first', 'last', False]),
            }
        )
    )
    def remove_duplicates(self, request, survey_id=None):
        """Remove duplicate rows from survey data."""
        try:
            df, survey = self._get_dataframe(survey_id)
            subset = request.data.get('subset')
            keep = request.data.get('keep', 'first')

            cleaning_service = DataCleaningService(df)
            df_modified, report = cleaning_service.remove_duplicates(subset=subset, keep=keep)

            preview_service = DataCleaningService(df_modified)
            preview = preview_service.get_preview_data(page=1, page_size=50)

            return Response({
                'report': report,
                'preview': preview
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Handle missing values in survey data",
        operation_summary="Handle missing values",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'strategy': openapi.Schema(type=openapi.TYPE_STRING),
                'columns': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                'fill_value': openapi.Schema(type=openapi.TYPE_STRING),
            }
        )
    )
    def handle_missing(self, request, survey_id=None):
        """Handle missing values in survey data."""
        try:
            df, survey = self._get_dataframe(survey_id)
            strategy = request.data.get('strategy')
            columns = request.data.get('columns')
            fill_value = request.data.get('fill_value')

            cleaning_service = DataCleaningService(df)
            df_modified, report = cleaning_service.handle_missing_values(
                strategy=strategy,
                columns=columns,
                fill_value=fill_value
            )

            preview_service = DataCleaningService(df_modified)
            preview = preview_service.get_preview_data(page=1, page_size=50)

            return Response({
                'report': report,
                'preview': preview
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Find and replace values in a column",
        operation_summary="Find and replace",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'column': openapi.Schema(type=openapi.TYPE_STRING),
                'find_value': openapi.Schema(type=openapi.TYPE_STRING),
                'replace_value': openapi.Schema(type=openapi.TYPE_STRING),
                'use_regex': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            }
        )
    )
    def find_replace(self, request, survey_id=None):
        """Find and replace values in a column."""
        try:
            df, survey = self._get_dataframe(survey_id)
            column = request.data.get('column')
            find_value = request.data.get('find_value')
            replace_value = request.data.get('replace_value')
            use_regex = request.data.get('use_regex', False)

            cleaning_service = DataCleaningService(df)
            df_modified, report = cleaning_service.find_replace(
                column=column,
                find_value=find_value,
                replace_value=replace_value,
                use_regex=use_regex
            )

            preview_service = DataCleaningService(df_modified)
            preview = preview_service.get_preview_data(page=1, page_size=50)

            return Response({
                'report': report,
                'preview': preview
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Standardize data in columns",
        operation_summary="Standardize data",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'columns': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                'operations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
            }
        )
    )
    def standardize(self, request, survey_id=None):
        """Standardize data in specified columns."""
        try:
            df, survey = self._get_dataframe(survey_id)
            columns = request.data.get('columns', [])
            operations = request.data.get('operations', [])

            cleaning_service = DataCleaningService(df)
            df_modified, report = cleaning_service.standardize_data(
                columns=columns,
                operations=operations
            )

            preview_service = DataCleaningService(df_modified)
            preview = preview_service.get_preview_data(page=1, page_size=50)

            return Response({
                'report': report,
                'preview': preview
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Create a new variable/column",
        operation_summary="Create variable",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'new_column': openapi.Schema(type=openapi.TYPE_STRING),
                'expression': openapi.Schema(type=openapi.TYPE_STRING),
                'source_columns': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                'operation': openapi.Schema(type=openapi.TYPE_STRING),
            }
        )
    )
    def create_variable(self, request, survey_id=None):
        """Create a new variable/column based on existing columns."""
        try:
            df, survey = self._get_dataframe(survey_id)
            new_column = request.data.get('new_column')
            expression = request.data.get('expression')
            source_columns = request.data.get('source_columns')
            operation = request.data.get('operation')

            cleaning_service = DataCleaningService(df)
            df_modified, report = cleaning_service.create_variable(
                new_column=new_column,
                expression=expression,
                source_columns=source_columns,
                operation=operation
            )

            preview_service = DataCleaningService(df_modified)
            preview = preview_service.get_preview_data(page=1, page_size=50)

            return Response({
                'report': report,
                'preview': preview
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Save cleaned data back to survey",
        operation_summary="Save cleaned data",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'cleaned_data': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
            }
        )
    )
    def save_cleaned(self, request, survey_id=None):
        """Save cleaned data back to the survey."""
        try:
            survey = Survey.objects.get(id=survey_id)
            cleaned_data = request.data.get('cleaned_data', [])

            if not cleaned_data:
                return Response(
                    {'error': 'No cleaned data provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Delete existing survey data
            SurveyData.objects.filter(survey=survey).delete()

            # Create new survey data entries
            for record in cleaned_data:
                SurveyData.objects.create(
                    survey=survey,
                    data=record,
                    cleaned=True,
                    cleaned_by=request.user
                )

            # Update survey metadata
            survey.cleaned = True
            survey.cleaned_by = request.user
            survey.cleaned_records = len(cleaned_data)
            survey.save()

            return Response({
                'success': True,
                'message': f'Successfully saved {len(cleaned_data)} cleaned records',
                'survey_id': survey.id
            }, status=status.HTTP_200_OK)

        except Survey.DoesNotExist:
            return Response(
                {'error': 'Survey not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )