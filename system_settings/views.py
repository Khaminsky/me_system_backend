from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import SystemSettings
from .serializers import SystemSettingsSerializer, SystemSettingsPublicSerializer


class SystemSettingsView(APIView):
    """
    GET: Retrieve system settings (admin only)
    PUT/PATCH: Update system settings (admin only)
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        """Get current system settings"""
        # Check if user is admin
        if not request.user.is_staff and request.user.role != 'admin':
            return Response(
                {'error': 'Only administrators can view system settings'},
                status=status.HTTP_403_FORBIDDEN
            )

        settings = SystemSettings.load()
        serializer = SystemSettingsSerializer(settings, context={'request': request})
        return Response(serializer.data)

    def put(self, request):
        """Update system settings (full update)"""
        return self._update_settings(request, partial=False)

    def patch(self, request):
        """Update system settings (partial update)"""
        return self._update_settings(request, partial=True)

    def _update_settings(self, request, partial=False):
        """Helper method to update settings"""
        # Check if user is admin
        if not request.user.is_staff and request.user.role != 'admin':
            return Response(
                {'error': 'Only administrators can update system settings'},
                status=status.HTTP_403_FORBIDDEN
            )

        settings = SystemSettings.load()
        serializer = SystemSettingsSerializer(
            settings,
            data=request.data,
            partial=partial,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SystemSettingsPublicView(APIView):
    """
    GET: Retrieve public system settings (no authentication required)
    Used for branding, theme, and public configuration
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Get public system settings"""
        settings = SystemSettings.load()
        serializer = SystemSettingsPublicSerializer(settings, context={'request': request})
        return Response(serializer.data)
