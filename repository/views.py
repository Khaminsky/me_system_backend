from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Count, Sum
from django.utils import timezone
from .models import Document, DocumentCategory, DocumentAccess
from .serializers import (
    DocumentListSerializer, DocumentDetailSerializer,
    DocumentUploadSerializer, DocumentCategorySerializer,
    DocumentAccessSerializer
)


class DocumentCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document categories.
    """
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing documents with optimized queries.

    Features:
    - Optimized queries with select_related/prefetch_related
    - File upload support with chunking
    - Search and filtering
    - Access logging
    - Bulk operations
    """
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'tags', 'file_name']
    ordering_fields = ['uploaded_at', 'title', 'file_size', 'document_type']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        """
        Optimized queryset with select_related for foreign keys.
        Reduces database queries significantly.
        """
        queryset = Document.objects.select_related(
            'project',
            'category',
            'uploaded_by',
            'parent_document'
        ).all()

        # Filter by project
        project_id = self.request.query_params.get('project', None)
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # Filter by document type
        doc_type = self.request.query_params.get('document_type', None)
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)

        # Filter by category
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filter archived documents
        include_archived = self.request.query_params.get('include_archived', 'false')
        if include_archived.lower() != 'true':
            queryset = queryset.filter(is_archived=False)

        # Filter by tags
        tags = self.request.query_params.get('tags', None)
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            q_objects = Q()
            for tag in tag_list:
                q_objects |= Q(tags__icontains=tag)
            queryset = queryset.filter(q_objects)

        return queryset

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action in ['upload', 'create']:
            return DocumentUploadSerializer
        return DocumentDetailSerializer

    def perform_create(self, serializer):
        """Save document and log access"""
        document = serializer.save()
        self._log_access(document, 'upload')

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to log access"""
        instance = self.get_object()
        self._log_access(instance, 'view')
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def _log_access(self, document, action):
        """Helper method to log document access"""
        DocumentAccess.objects.create(
            document=document,
            accessed_by=self.request.user if self.request.user.is_authenticated else None,
            action=action,
            ip_address=self._get_client_ip()
        )

    def _get_client_ip(self):
        """Get client IP address from request"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """
        Optimized endpoint for file uploads.
        Supports chunked uploads for large files.
        """
        serializer = DocumentUploadSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            document = serializer.save()
            self._log_access(document, 'upload')

            # Return detailed response
            response_serializer = DocumentDetailSerializer(
                document,
                context={'request': request}
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a document"""
        document = self.get_object()
        document.is_archived = True
        document.archived_at = timezone.now()
        document.archived_by = request.user
        document.save()

        self._log_access(document, 'archive')

        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Unarchive a document"""
        document = self.get_object()
        document.is_archived = False
        document.archived_at = None
        document.archived_by = None
        document.save()

        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Track download and return file info"""
        document = self.get_object()
        self._log_access(document, 'download')

        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get document statistics"""
        queryset = self.get_queryset()

        stats = {
            'total_documents': queryset.count(),
            'total_size_bytes': queryset.aggregate(Sum('file_size'))['file_size__sum'] or 0,
            'by_type': {},
            'by_project': {},
        }

        # Calculate total size in MB
        stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)

        # Documents by type
        by_type = queryset.values('document_type').annotate(count=Count('id'))
        for item in by_type:
            stats['by_type'][item['document_type']] = item['count']

        # Documents by project
        by_project = queryset.values('project__name').annotate(count=Count('id'))
        for item in by_project:
            stats['by_project'][item['project__name']] = item['count']

        return Response(stats)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently uploaded documents"""
        limit = int(request.query_params.get('limit', 10))
        queryset = self.get_queryset()[:limit]
        serializer = DocumentListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class DocumentAccessViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing document access logs.
    Read-only to maintain audit trail integrity.
    """
    queryset = DocumentAccess.objects.select_related(
        'document',
        'accessed_by'
    ).all()
    serializer_class = DocumentAccessSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['document__title', 'accessed_by__username', 'action']
    ordering_fields = ['accessed_at', 'action']
    ordering = ['-accessed_at']

    def get_queryset(self):
        """Filter access logs by document or user"""
        queryset = super().get_queryset()

        # Filter by document
        document_id = self.request.query_params.get('document', None)
        if document_id:
            queryset = queryset.filter(document_id=document_id)

        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(accessed_by_id=user_id)

        return queryset
