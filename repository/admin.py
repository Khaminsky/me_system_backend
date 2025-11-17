from django.contrib import admin
from django.utils.html import format_html
from .models import Document, DocumentCategory, DocumentAccess


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """Admin interface for document categories"""
    list_display = ['name', 'description', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for documents with optimized display"""
    list_display = [
        'title', 'document_type', 'project', 'category',
        'file_size_display', 'uploaded_by', 'uploaded_at',
        'is_archived', 'version'
    ]
    list_filter = [
        'document_type', 'is_archived', 'uploaded_at',
        'category', 'is_public'
    ]
    search_fields = [
        'title', 'description', 'file_name', 'tags',
        'project__name'
    ]
    readonly_fields = [
        'file_name', 'file_size', 'file_size_display', 'mime_type',
        'file_hash', 'uploaded_by', 'uploaded_at', 'updated_at',
        'file_preview'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'document_type', 'category', 'tags')
        }),
        ('Project & Access', {
            'fields': ('project', 'is_public', 'is_archived')
        }),
        ('File Information', {
            'fields': (
                'file', 'file_preview', 'file_name', 'file_size',
                'file_size_display', 'mime_type', 'file_hash'
            )
        }),
        ('Version Control', {
            'fields': ('version', 'parent_document'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'uploaded_by', 'uploaded_at', 'updated_at',
                'archived_at', 'archived_by'
            ),
            'classes': ('collapse',)
        }),
    )

    # Optimize queries
    list_select_related = ['project', 'category', 'uploaded_by']

    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.2f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "N/A"
    file_size_display.short_description = 'File Size'

    def file_preview(self, obj):
        """Show file preview for images"""
        if obj.file and obj.extension in ['png', 'jpg', 'jpeg', 'gif']:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.file.url
            )
        return "No preview available"
    file_preview.short_description = 'Preview'

    def save_model(self, request, obj, form, change):
        if not change:  # Only set uploaded_by on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    """Admin interface for document access logs"""
    list_display = [
        'document', 'accessed_by', 'action',
        'accessed_at', 'ip_address'
    ]
    list_filter = ['action', 'accessed_at']
    search_fields = [
        'document__title', 'accessed_by__username',
        'ip_address'
    ]
    readonly_fields = [
        'document', 'accessed_by', 'accessed_at',
        'ip_address', 'action'
    ]

    # Optimize queries
    list_select_related = ['document', 'accessed_by']

    # Make all fields read-only to preserve audit trail
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
