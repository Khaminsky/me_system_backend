from django.shortcuts import render
from django.utils import timezone
from pandas import read_excel, read_csv
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
            else:
                df = read_excel(file_obj)

            # Check if dataframe is empty
            if df.empty:
                survey.delete()
                return Response({'error': 'File is empty'}, status=status.HTTP_400_BAD_REQUEST)

            # Create SurveyData records
            for _, row in df.iterrows():
                SurveyData.objects.create(
                    survey=survey,
                    data=row.to_dict()
                )

            survey.total_records = len(df)
            survey.save()

            serializer = SurveySerializer(survey)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error reading file: {e}")
            # Delete the survey if file processing fails
            survey.delete()
            return Response({'error': f'Error reading file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
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