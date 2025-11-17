from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Project
from .serializers import ProjectSerializer
from surveys.serializers import SurveySerializer
from users.permissions import CanUploadSurvey, CanViewReports


class ProjectListView(APIView):
    permission_classes = [IsAuthenticated, CanViewReports]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all active projects",
        operation_summary="List all projects",
        responses={200: ProjectSerializer(many=True)}
    )
    def get(self, request):
        """
        Get all active (non-archived) projects in the system.
        """
        projects = Project.objects.filter(is_archived=False)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create a new project",
        operation_summary="Create project",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Project name'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Project description'),
            },
            required=['name']
        ),
        responses={201: ProjectSerializer(), 400: openapi.Response('Bad request')}
    )
    def post(self, request):
        """
        Create a new project.
        """
        name = request.data.get('name')
        description = request.data.get('description', '')

        if not name:
            return Response({'error': 'Project name is required'}, status=status.HTTP_400_BAD_REQUEST)

        project = Project.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )

        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated, CanUploadSurvey]

    @swagger_auto_schema(
        operation_description="Retrieve a specific project by ID",
        operation_summary="Get project details",
        responses={200: ProjectSerializer(), 404: openapi.Response('Project not found')}
    )
    def get(self, request, project_id):
        """
        Get a specific project by ID (only if not archived).
        """
        try:
            project = Project.objects.get(id=project_id, is_archived=False)
            serializer = ProjectSerializer(project)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update a project (full update)",
        operation_summary="Update project details",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Project name'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Project description'),
            },
            required=['name']
        ),
        responses={200: ProjectSerializer(), 404: openapi.Response('Project not found'), 400: openapi.Response('Bad request')}
    )
    def put(self, request, project_id):
        """
        Update a project (name and description).
        """
        try:
            project = Project.objects.get(id=project_id, is_archived=False)

            if 'name' in request.data:
                project.name = request.data['name']
            if 'description' in request.data:
                project.description = request.data['description']

            project.save()
            serializer = ProjectSerializer(project)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Partially update a project",
        operation_summary="Partial update project",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Project name'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Project description'),
            }
        ),
        responses={200: ProjectSerializer(), 404: openapi.Response('Project not found'), 400: openapi.Response('Bad request')}
    )
    def patch(self, request, project_id):
        """
        Partially update a project (name and/or description).
        """
        try:
            project = Project.objects.get(id=project_id, is_archived=False)

            if 'name' in request.data:
                project.name = request.data['name']
            if 'description' in request.data:
                project.description = request.data['description']

            project.save()
            serializer = ProjectSerializer(project)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Archive (soft delete) a project",
        operation_summary="Archive project",
        responses={204: openapi.Response('Project archived successfully'), 404: openapi.Response('Project not found')}
    )
    def delete(self, request, project_id):
        """
        Archive a project (soft delete - marks as archived instead of deleting).
        """
        try:
            project = Project.objects.get(id=project_id, is_archived=False)
            project.is_archived = True
            project.archived_date = timezone.now()
            project.archived_by = request.user
            project.save()
            return Response({'message': 'Project archived successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)


class ProjectArchivedListView(APIView):
    permission_classes = [IsAuthenticated, CanViewReports]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all archived projects",
        operation_summary="List archived projects",
        responses={200: ProjectSerializer(many=True)}
    )
    def get(self, request):
        """
        Get all archived projects in the system.
        """
        projects = Project.objects.filter(is_archived=True)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectRestoreView(APIView):
    permission_classes = [IsAuthenticated, CanUploadSurvey]

    @swagger_auto_schema(
        operation_description="Restore an archived project",
        operation_summary="Restore project",
        responses={200: ProjectSerializer(), 404: openapi.Response('Project not found')}
    )
    def post(self, request, project_id):
        """
        Restore an archived project back to active status.
        """
        try:
            project = Project.objects.get(id=project_id, is_archived=True)
            project.is_archived = False
            project.archived_date = None
            project.archived_by = None
            project.save()
            serializer = ProjectSerializer(project)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({'error': 'Archived project not found'}, status=status.HTTP_404_NOT_FOUND)


class ProjectSurveysView(APIView):
    permission_classes = [IsAuthenticated, CanViewReports]

    @swagger_auto_schema(
        operation_description="Retrieve all surveys for a specific project",
        operation_summary="List project surveys",
        responses={200: SurveySerializer(many=True), 404: openapi.Response('Project not found')}
    )
    def get(self, request, project_id):
        """
        Get all active surveys for a specific project.
        """
        try:
            project = Project.objects.get(id=project_id, is_archived=False)
            surveys = project.surveys.filter(is_archived=False)
            serializer = SurveySerializer(surveys, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
