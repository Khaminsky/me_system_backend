from django.shortcuts import render
from django.utils import timezone
from pandas import read_excel, read_csv
import pandas as pd
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from surveys.models import Survey, SurveyData
from .serializers import SurveySerializer
from users.permissions import CanUploadSurvey, CanViewReports

# Create your views here.
class SurveyUploadView(APIView):
    permission_classes = [IsAuthenticated, CanUploadSurvey]

    @swagger_auto_schema(
        operation_description="Upload a survey file (CSV or Excel format)",
        operation_summary="Upload survey data",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'file': openapi.Schema(type=openapi.TYPE_FILE, description='Survey file'),
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Survey name'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Survey description'),
            },
            required=['file']
        ),
        responses={201: openapi.Response('Survey uploaded successfully')}
    )
    def post(self, request):
        # Check if file is provided
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES['file']

        # Validate file format
        if not file_obj.name.endswith(('.csv', '.xlsx', '.xls')):
            return Response({'error': 'File must be CSV or Excel format'}, status=status.HTTP_400_BAD_REQUEST)

        name = request.data.get('name', file_obj.name)
        description = request.data.get('description', '')

        survey = Survey.objects.create(
            name=name,
            description=description,
            uploaded_by=request.user,
            file=file_obj
        )

        try:
            # Seek to beginning of file
            file_obj.seek(0)

            # Read file based on format
            if file_obj.name.endswith('.csv'):
                df = read_csv(file_obj)

                # Check if dataframe is empty
                if df.empty:
                    survey.delete()
                    return Response({'error': 'File is empty'}, status=status.HTTP_400_BAD_REQUEST)

                # Create SurveyData records
                for _, row in df.iterrows():
                    # Convert numpy types to native Python types
                    row_dict = {}
                    for key, value in row.to_dict().items():
                        if pd.isna(value):
                            row_dict[key] = None
                        elif isinstance(value, (np.integer, np.floating)):
                            row_dict[key] = value.item()
                        elif isinstance(value, (pd.Timestamp, np.datetime64)):
                            # Convert datetime/Timestamp to ISO format string
                            row_dict[key] = pd.Timestamp(value).isoformat()
                        else:
                            row_dict[key] = str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value

                    SurveyData.objects.create(
                        survey=survey,
                        data=row_dict
                    )

                survey.total_records = len(df)
                survey.save()

                serializer = SurveySerializer(survey)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            else:  # Excel file
                # Determine the correct engine based on file extension
                if file_obj.name.endswith('.xls'):
                    engine = 'xlrd'  # For old Excel format (Excel 97-2003)
                else:
                    engine = 'openpyxl'  # For new Excel format (.xlsx)

                # Check for multiple sheets
                excel_file = pd.ExcelFile(file_obj, engine=engine)
                sheet_names = excel_file.sheet_names

                if len(sheet_names) > 1:
                    # Multiple sheets - return sheet names for user selection
                    survey.save()
                    serializer = SurveySerializer(survey)
                    return Response({
                        'survey': serializer.data,
                        'requires_sheet_selection': True,
                        'sheet_names': sheet_names,
                        'message': 'Excel file contains multiple sheets. Please select a sheet to import.'
                    }, status=status.HTTP_200_OK)

                # Single sheet - process immediately
                df = read_excel(file_obj, sheet_name=0, engine=engine)

                # Check if dataframe is empty
                if df.empty:
                    survey.delete()
                    return Response({'error': 'File is empty'}, status=status.HTTP_400_BAD_REQUEST)

                # Create SurveyData records
                for _, row in df.iterrows():
                    # Convert numpy types to native Python types
                    row_dict = {}
                    for key, value in row.to_dict().items():
                        if pd.isna(value):
                            row_dict[key] = None
                        elif isinstance(value, (np.integer, np.floating)):
                            row_dict[key] = value.item()
                        elif isinstance(value, (pd.Timestamp, np.datetime64)):
                            # Convert datetime/Timestamp to ISO format string
                            row_dict[key] = pd.Timestamp(value).isoformat()
                        else:
                            row_dict[key] = str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value

                    SurveyData.objects.create(
                        survey=survey,
                        data=row_dict
                    )

                survey.total_records = len(df)
                survey.save()

                serializer = SurveySerializer(survey)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Error reading file: {e}")
            import traceback
            traceback.print_exc()
            # Delete the survey if file processing fails
            survey.delete()
            return Response({'error': f'Error reading file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class SurveyProcessSheetView(APIView):
    """Process one or more sheets from an Excel file that was already uploaded"""
    permission_classes = [IsAuthenticated, CanUploadSurvey]

    @swagger_auto_schema(
        operation_description="Process one or more sheets from an uploaded Excel file",
        operation_summary="Process Excel sheet(s)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'sheet_names': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description='Array of sheet names to process'
                ),
            },
        ),
        responses={
            200: SurveySerializer(),
            404: openapi.Response('Survey not found'),
            400: openapi.Response('Bad request')
        }
    )
    def post(self, request, survey_id):
        """
        Process one or more sheets from an already-uploaded Excel file.
        Provide an array of sheet_names to process.
        All selected sheets will be combined into one survey.
        """
        try:
            survey = Survey.objects.get(id=survey_id, is_archived=False)
        except Survey.DoesNotExist:
            return Response({'error': 'Survey not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if file is Excel
        if not survey.file.name.endswith(('.xlsx', '.xls')):
            return Response({'error': 'Survey file is not an Excel file'}, status=status.HTTP_400_BAD_REQUEST)

        # Get sheet names
        sheet_names = request.data.get('sheet_names', [])

        if not sheet_names or not isinstance(sheet_names, list):
            return Response({'error': 'sheet_names must be a non-empty array'}, status=status.HTTP_400_BAD_REQUEST)

        # Determine the correct engine based on file extension
        if survey.file.name.endswith('.xls'):
            engine = 'xlrd'  # For old Excel format (Excel 97-2003)
        else:
            engine = 'openpyxl'  # For new Excel format (.xlsx)

        try:
            # Delete existing SurveyData records if any
            SurveyData.objects.filter(survey=survey).delete()

            total_records = 0

            # Process each selected sheet
            for sheet_name in sheet_names:
                try:
                    # Read the specific sheet
                    df = read_excel(survey.file.path, sheet_name=sheet_name, engine=engine)

                    # Skip empty sheets
                    if df.empty:
                        continue

                    # Create SurveyData records for this sheet
                    for _, row in df.iterrows():
                        # Convert numpy types to native Python types
                        row_dict = {}
                        for key, value in row.to_dict().items():
                            if pd.isna(value):
                                row_dict[key] = None
                            elif isinstance(value, (np.integer, np.floating)):
                                row_dict[key] = value.item()
                            elif isinstance(value, (pd.Timestamp, np.datetime64)):
                                # Convert datetime/Timestamp to ISO format string
                                row_dict[key] = pd.Timestamp(value).isoformat()
                            else:
                                row_dict[key] = str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value

                        SurveyData.objects.create(
                            survey=survey,
                            data=row_dict,
                            sheet_name=sheet_name  # Track which sheet this data came from
                        )

                    total_records += len(df)

                except ValueError as e:
                    # Skip invalid sheet names
                    print(f"Skipping invalid sheet '{sheet_name}': {e}")
                    continue

            # Check if any data was imported
            if total_records == 0:
                return Response({'error': 'No data found in selected sheets'}, status=status.HTTP_400_BAD_REQUEST)

            survey.total_records = total_records
            survey.save()

            serializer = SurveySerializer(survey)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error processing sheets: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': f'Error processing sheets: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class SurveyListView(APIView):
    permission_classes = [IsAuthenticated, CanViewReports]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all active surveys",
        operation_summary="List all surveys",
        responses={200: SurveySerializer(many=True)}
    )
    def get(self, request):
        """
        Get all active (non-archived) surveys in the system.
        """
        surveys = Survey.objects.filter(is_archived=False)
        serializer = SurveySerializer(surveys, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SurveyDetailView(APIView):
    permission_classes = [IsAuthenticated, CanUploadSurvey]

    @swagger_auto_schema(
        operation_description="Retrieve a specific survey by ID",
        operation_summary="Get survey details",
        responses={200: SurveySerializer(), 404: openapi.Response('Survey not found')}
    )
    def get(self, request, survey_id):
        """
        Get a specific survey by ID (only if not archived).
        """
        try:
            survey = Survey.objects.get(id=survey_id, is_archived=False)
            serializer = SurveySerializer(survey)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Survey.DoesNotExist:
            return Response({'error': 'Survey not found'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update a survey (full update)",
        operation_summary="Update survey details",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Survey name'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Survey description'),
                'file': openapi.Schema(type=openapi.TYPE_FILE, description='Survey file (CSV or Excel)'),
            },
            required=['name']
        ),
        responses={200: SurveySerializer(), 404: openapi.Response('Survey not found'), 400: openapi.Response('Bad request')}
    )
    def put(self, request, survey_id):
        """
        Update a survey (name, description, and optionally file).
        If a new file is provided, it will replace the existing one and re-process the data.
        """
        try:
            survey = Survey.objects.get(id=survey_id, is_archived=False)

            if 'name' in request.data:
                survey.name = request.data['name']
            if 'description' in request.data:
                survey.description = request.data['description']

            # Handle file upload if provided
            if 'file' in request.FILES:
                file_obj = request.FILES['file']
                if not file_obj.name.endswith(('.csv', '.xlsx', '.xls')):
                    return Response({'error': 'File must be CSV or Excel format'}, status=status.HTTP_400_BAD_REQUEST)

                survey.file = file_obj

                try:
                    # Clear existing survey data
                    SurveyData.objects.filter(survey=survey).delete()

                    # Re-process the file
                    df = read_excel(file_obj)
                    for _, row in df.iterrows():
                        SurveyData.objects.create(
                            survey=survey,
                            data=row.to_dict()
                        )
                    survey.total_records = len(df)
                except Exception as e:
                    return Response({'error': f'Error reading file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

            survey.save()
            serializer = SurveySerializer(survey)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Survey.DoesNotExist:
            return Response({'error': 'Survey not found'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Partially update a survey",
        operation_summary="Partial update survey",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Survey name'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Survey description'),
                'file': openapi.Schema(type=openapi.TYPE_FILE, description='Survey file (CSV or Excel)'),
            }
        ),
        responses={200: SurveySerializer(), 404: openapi.Response('Survey not found'), 400: openapi.Response('Bad request')}
    )
    def patch(self, request, survey_id):
        """
        Partially update a survey (name, description, and/or file).
        If a new file is provided, it will replace the existing one and re-process the data.
        """
        try:
            survey = Survey.objects.get(id=survey_id, is_archived=False)

            if 'name' in request.data:
                survey.name = request.data['name']
            if 'description' in request.data:
                survey.description = request.data['description']

            # Handle file upload if provided
            if 'file' in request.FILES:
                file_obj = request.FILES['file']
                if not file_obj.name.endswith(('.csv', '.xlsx', '.xls')):
                    return Response({'error': 'File must be CSV or Excel format'}, status=status.HTTP_400_BAD_REQUEST)

                survey.file = file_obj

                try:
                    # Clear existing survey data
                    SurveyData.objects.filter(survey=survey).delete()

                    # Re-process the file
                    df = read_excel(file_obj)
                    for _, row in df.iterrows():
                        SurveyData.objects.create(
                            survey=survey,
                            data=row.to_dict()
                        )
                    survey.total_records = len(df)
                except Exception as e:
                    return Response({'error': f'Error reading file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

            survey.save()
            serializer = SurveySerializer(survey)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Survey.DoesNotExist:
            return Response({'error': 'Survey not found'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Archive (soft delete) a survey",
        operation_summary="Archive survey",
        responses={204: openapi.Response('Survey archived successfully'), 404: openapi.Response('Survey not found')}
    )
    def delete(self, request, survey_id):
        """
        Archive a survey (soft delete - marks as archived instead of deleting).
        """
        try:
            survey = Survey.objects.get(id=survey_id, is_archived=False)
            survey.is_archived = True
            survey.archived_date = timezone.now()
            survey.archived_by = request.user
            survey.save()
            return Response({'message': 'Survey archived successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Survey.DoesNotExist:
            return Response({'error': 'Survey not found'}, status=status.HTTP_404_NOT_FOUND)


class SurveyArchivedListView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve a list of all archived surveys",
        operation_summary="List archived surveys",
        responses={200: SurveySerializer(many=True)}
    )
    def get(self, request):
        """
        Get all archived surveys in the system.
        """
        surveys = Survey.objects.filter(is_archived=True)
        serializer = SurveySerializer(surveys, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SurveyRestoreView(APIView):
    @swagger_auto_schema(
        operation_description="Restore an archived survey",
        operation_summary="Restore survey",
        responses={200: SurveySerializer(), 404: openapi.Response('Survey not found')}
    )
    def post(self, request, survey_id):
        """
        Restore an archived survey back to active status.
        """
        try:
            survey = Survey.objects.get(id=survey_id, is_archived=True)
            survey.is_archived = False
            survey.archived_date = None
            survey.archived_by = None
            survey.save()
            serializer = SurveySerializer(survey)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Survey.DoesNotExist:
            return Response({'error': 'Archived survey not found'}, status=status.HTTP_404_NOT_FOUND)


class SurveyFieldsView(APIView):
    """
    API endpoint to get metadata about all fields in a survey.
    Useful for building indicators and formulas.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get metadata for all fields in a survey including types, statistics, and sample values",
        operation_summary="Get survey field metadata",
        responses={
            200: openapi.Response('Field metadata retrieved successfully'),
            404: openapi.Response('Survey not found'),
            400: openapi.Response('Error processing survey data')
        }
    )
    def get(self, request, survey_id):
        """
        Get field metadata for a survey.
        Returns field names, types, statistics, and sample values.
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

            # Analyze each field
            fields_metadata = []

            for column in df.columns:
                field_meta = {
                    'name': column,
                    'null_count': int(df[column].isnull().sum()),
                    'non_null_count': int(df[column].notna().sum()),
                }

                # Get sample values (first 5 non-null unique values)
                sample_values = df[column].dropna().unique()[:5].tolist()
                field_meta['sample_values'] = sample_values

                # Try to determine if numeric
                try:
                    numeric_data = pd.to_numeric(df[column], errors='coerce')
                    if numeric_data.notna().sum() > 0:
                        field_meta['type'] = 'numeric'
                        field_meta['min'] = float(numeric_data.min())
                        field_meta['max'] = float(numeric_data.max())
                        field_meta['mean'] = float(numeric_data.mean())
                        field_meta['median'] = float(numeric_data.median())
                        field_meta['std'] = float(numeric_data.std()) if numeric_data.std() == numeric_data.std() else None  # Check for NaN
                    else:
                        # Categorical field
                        field_meta['type'] = 'categorical'
                        field_meta['unique_count'] = int(df[column].nunique())
                        # Get value counts for categorical fields
                        value_counts = df[column].value_counts().head(10).to_dict()
                        field_meta['value_counts'] = {str(k): int(v) for k, v in value_counts.items()}
                except:
                    # Categorical field
                    field_meta['type'] = 'categorical'
                    field_meta['unique_count'] = int(df[column].nunique())
                    # Get value counts for categorical fields
                    value_counts = df[column].value_counts().head(10).to_dict()
                    field_meta['value_counts'] = {str(k): int(v) for k, v in value_counts.items()}

                fields_metadata.append(field_meta)

            return Response({
                'survey_id': survey_id,
                'survey_name': survey.name,
                'total_records': len(df),
                'total_fields': len(df.columns),
                'fields': fields_metadata
            }, status=status.HTTP_200_OK)

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