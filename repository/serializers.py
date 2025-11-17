from rest_framework import serializers
from .models import Document, DocumentCategory, DocumentAccess
from projects.models import Project
from django.contrib.auth import get_user_model

User = get_user_model()


class DocumentCategorySerializer(serializers.ModelSerializer):
    """Serializer for document categories"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = DocumentCategory
        fields = [
            'id', 'name', 'description', 'created_at', 
            'created_by', 'created_by_name'
        ]
        read_only_fields = ['created_at', 'created_by']


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing documents"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    file_size_mb = serializers.ReadOnlyField()
    extension = serializers.ReadOnlyField()

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'document_type', 'project', 'project_name',
            'category', 'category_name', 'file_name', 'file_size', 
            'file_size_mb', 'extension', 'mime_type', 'uploaded_by',
            'uploaded_by_name', 'uploaded_at', 'is_archived', 'version',
            'tags'
        ]


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for document CRUD operations"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    file_size_mb = serializers.ReadOnlyField()
    extension = serializers.ReadOnlyField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'document_type', 'project', 
            'project_name', 'category', 'category_name', 'file', 'file_url',
            'file_name', 'file_size', 'file_size_mb', 'extension', 
            'mime_type', 'file_hash', 'version', 'parent_document',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at', 'updated_at',
            'is_public', 'is_archived', 'archived_at', 'archived_by', 'tags'
        ]
        read_only_fields = [
            'file_name', 'file_size', 'mime_type', 'file_hash',
            'uploaded_by', 'uploaded_at', 'updated_at'
        ]

    def get_file_url(self, obj):
        """Get the full URL for the file"""
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def create(self, validated_data):
        """Override create to set uploaded_by and compute mime_type"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['uploaded_by'] = request.user
        
        # Set mime_type from uploaded file
        file_obj = validated_data.get('file')
        if file_obj:
            validated_data['mime_type'] = file_obj.content_type or 'application/octet-stream'
        
        return super().create(validated_data)


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Optimized serializer for file uploads"""
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'document_type', 'project',
            'category', 'file', 'is_public', 'tags'
        ]

    def create(self, validated_data):
        """Handle file upload with metadata extraction"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['uploaded_by'] = request.user
        
        # Extract file metadata
        file_obj = validated_data.get('file')
        if file_obj:
            validated_data['mime_type'] = file_obj.content_type or 'application/octet-stream'
            validated_data['file_size'] = file_obj.size
            validated_data['file_name'] = file_obj.name
        
        return super().create(validated_data)


class DocumentAccessSerializer(serializers.ModelSerializer):
    """Serializer for document access logs"""
    document_title = serializers.CharField(source='document.title', read_only=True)
    accessed_by_name = serializers.CharField(source='accessed_by.username', read_only=True)

    class Meta:
        model = DocumentAccess
        fields = [
            'id', 'document', 'document_title', 'accessed_by',
            'accessed_by_name', 'accessed_at', 'ip_address', 'action'
        ]
        read_only_fields = ['accessed_at']

