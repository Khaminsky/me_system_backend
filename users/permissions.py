"""
Role-based Permission Classes

Provides permission classes for role-based access control (RBAC).
Supports Admin, Analyst, and Viewer roles.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Permission class for Admin role.
    Admins have full access to all resources.
    """
    message = "Only administrators can access this resource."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


class IsAnalyst(BasePermission):
    """
    Permission class for Analyst role.
    Analysts can upload surveys, validate data, and compute indicators.
    """
    message = "Only analysts can access this resource."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['admin', 'analyst']
        )


class IsViewer(BasePermission):
    """
    Permission class for Viewer role.
    Viewers can only view reports and dashboards.
    """
    message = "Only viewers can access this resource."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['admin', 'analyst', 'viewer']
        )


class CanUploadSurvey(BasePermission):
    """
    Permission class for survey upload.
    Only Admins and Analysts can upload surveys.
    """
    message = "You do not have permission to upload surveys."

    def has_permission(self, request, view):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return (
                request.user and
                request.user.is_authenticated and
                request.user.role in ['admin', 'analyst']
            )
        return (
            request.user and
            request.user.is_authenticated
        )


class CanValidateData(BasePermission):
    """
    Permission class for data validation.
    Only Admins and Analysts can validate data.
    """
    message = "You do not have permission to validate data."

    def has_permission(self, request, view):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return (
                request.user and
                request.user.is_authenticated and
                request.user.role in ['admin', 'analyst']
            )
        return (
            request.user and
            request.user.is_authenticated
        )


class CanComputeIndicators(BasePermission):
    """
    Permission class for indicator computation.
    Only Admins and Analysts can compute indicators.
    """
    message = "You do not have permission to compute indicators."

    def has_permission(self, request, view):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return (
                request.user and
                request.user.is_authenticated and
                request.user.role in ['admin', 'analyst']
            )
        return (
            request.user and
            request.user.is_authenticated
        )


class CanGenerateReports(BasePermission):
    """
    Permission class for report generation.
    Only Admins and Analysts can generate reports.
    """
    message = "You do not have permission to generate reports."

    def has_permission(self, request, view):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return (
                request.user and
                request.user.is_authenticated and
                request.user.role in ['admin', 'analyst']
            )
        return (
            request.user and
            request.user.is_authenticated
        )


class CanViewReports(BasePermission):
    """
    Permission class for viewing reports.
    All authenticated users can view reports.
    """
    message = "You do not have permission to view reports."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated
        )


class CanManageUsers(BasePermission):
    """
    Permission class for user management.
    Only Admins can manage users.
    """
    message = "Only administrators can manage users."

    def has_permission(self, request, view):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return (
                request.user and
                request.user.is_authenticated and
                request.user.role == 'admin'
            )
        return (
            request.user and
            request.user.is_authenticated
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Permission class for object-level permissions.
    Users can only modify their own objects, or admins can modify any object.
    """
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        # Allow admins to access any object
        if request.user.role == 'admin':
            return True

        # Allow users to access their own objects
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False

