from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from projects.models import Project
import os
import hashlib
from datetime import datetime


def document_upload_path(instance, filename):
    """
    Generate organized upload path for documents.
    Format: documents/{project_id}/{year}/{month}/{filename}
    """
    now = datetime.now()
    project_id = instance.project.id if instance.project else 'unassigned'
    return f'documents/{project_id}/{now.year}/{now.month:02d}/{filename}'


class DocumentCategory(models.Model):
    """Categories for organizing documents"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_categories'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Document Categories'
        ordering = ['name']


class Document(models.Model):
    """
    Model for storing project documents with optimized performance.
    Supports: PDF, Word, Excel, Images
    """
    DOCUMENT_TYPES = [
        ('proposal', 'Proposal'),
        ('contract', 'Contract'),
        ('report', 'Report'),
        ('presentation', 'Presentation'),
        ('spreadsheet', 'Spreadsheet'),
        ('image', 'Image'),
        ('other', 'Other'),
    ]

    # Allowed file extensions for validation
    ALLOWED_EXTENSIONS = [
        'pdf', 'doc', 'docx', 'xls', 'xlsx',
        'ppt', 'pptx', 'png', 'jpg', 'jpeg', 'gif', 'bmp'
    ]

    # Core fields
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='documents',
        db_index=True  # Index for fast project-based queries
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        db_index=True  # Index for filtering by type
    )
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )

    # File fields
    file = models.FileField(
        upload_to=document_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS)]
    )
    file_name = models.CharField(max_length=255)  # Original filename
    file_size = models.BigIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)
    file_hash = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,  # Index for deduplication checks
        help_text="SHA-256 hash for file integrity and deduplication"
    )

    # Version control
    version = models.PositiveIntegerField(default=1)
    parent_document = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions'
    )

    # Metadata
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Access control
    is_public = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_documents'
    )

    # Tags for better organization
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags for categorization"
    )

    def __str__(self):
        return f"{self.title} ({self.document_type})"

    def save(self, *args, **kwargs):
        """Override save to compute file metadata"""
        if self.file:
            # Store original filename
            if not self.file_name:
                self.file_name = os.path.basename(self.file.name)

            # Compute file size
            if not self.file_size:
                self.file_size = self.file.size

            # Compute file hash for integrity and deduplication
            if not self.file_hash:
                self.file_hash = self._compute_file_hash()

        super().save(*args, **kwargs)

    def _compute_file_hash(self):
        """Compute SHA-256 hash of the file"""
        sha256_hash = hashlib.sha256()
        for chunk in self.file.chunks():
            sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    @property
    def file_size_mb(self):
        """Return file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def extension(self):
        """Get file extension"""
        return os.path.splitext(self.file_name)[1].lower().replace('.', '')

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['project', 'document_type']),
            models.Index(fields=['project', 'uploaded_at']),
            models.Index(fields=['uploaded_by', 'uploaded_at']),
        ]
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'


class DocumentAccess(models.Model):
    """Track document access for analytics and security"""
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    accessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    accessed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    action = models.CharField(
        max_length=20,
        choices=[
            ('view', 'View'),
            ('download', 'Download'),
            ('update', 'Update'),
            ('delete', 'Delete'),
        ]
    )

    def __str__(self):
        return f"{self.document.title} - {self.action} by {self.accessed_by}"

    class Meta:
        ordering = ['-accessed_at']
        verbose_name = 'Document Access Log'
        verbose_name_plural = 'Document Access Logs'
