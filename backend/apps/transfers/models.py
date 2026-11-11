import uuid

from django.db import models
from django.db.models import F, Q


class Transfer(models.Model):
    class Status(models.TextChoices):
        PENDING_UPLOAD = "PENDING_UPLOAD", "Pending upload"
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    share_code = models.CharField(
        max_length=8,
        unique=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_UPLOAD,
    )

    upload_deadline_at = models.DateTimeField()
    upload_completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    upload_token_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        editable=False,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "expires_at"],
                name="transfer_status_expiry_idx",
            ),
        ]

    def __str__(self):
        return self.share_code


class TransferFile(models.Model):
    class Status(models.TextChoices):
        PENDING_UPLOAD = "PENDING_UPLOAD", "Pending upload"
        UPLOADED = "UPLOADED", "Uploaded"
        SCANNING = "SCANNING", "Scanning"
        AVAILABLE = "AVAILABLE", "Available"
        REJECTED = "REJECTED", "Rejected"
        DELETED = "DELETED", "Deleted"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.CASCADE,
        related_name="files",
    )

    original_filename = models.CharField(max_length=255)
    object_key = models.CharField(
        max_length=512,
        unique=True,
    )

    declared_content_type = models.CharField(
        max_length=255,
        blank=True,
    )
    content_type = models.CharField(
        max_length=255,
        blank=True,
    )

    expected_size_bytes = models.PositiveBigIntegerField()
    size_bytes = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_UPLOAD,
    )

    max_downloads = models.PositiveSmallIntegerField(default=5)
    download_count = models.PositiveSmallIntegerField(default=0)

    uploaded_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    scanned_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    storage_deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["status"],
                name="transferfile_status_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(download_count__lte=F("max_downloads")),
                name="download_count_within_limit",
            ),
            models.CheckConstraint(
                condition=Q(max_downloads__gt=0),
                name="max_downloads_positive",
            ),
            models.CheckConstraint(
                condition=Q(expected_size_bytes__gt=0),
                name="expected_size_positive",
            ),
        ]

    def __str__(self):
        return self.original_filename
