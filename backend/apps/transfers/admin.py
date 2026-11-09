
from django.contrib import admin
from django.utils.html import format_html
from django.utils.timesince import timesince
from django.utils import timezone

from .models import Transfer, TransferFile


class TransferFileInline(admin.TabularInline):
    model = TransferFile
    extra = 0
    can_delete = False
    show_change_link = True

    fields = (
        "original_filename",
        "status",
        "size_bytes",
        "download_count",
        "max_downloads",
        "uploaded_at",
        "scanned_at",
    )

    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = (
        "share_code",
        "status_badge",
        "file_count",
        "created_at",
        "expires_at",
        "expiry_status",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "share_code",
        "id",
    )

    readonly_fields = (
        "id",
        "share_code",
        "status",
        "upload_deadline_at",
        "upload_completed_at",
        "expires_at",
        "created_at",
    )

    inlines = (TransferFileInline,)

    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("files")

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        colors = {
            Transfer.Status.PENDING_UPLOAD: "#d97706",
            Transfer.Status.ACTIVE: "#16a34a",
            Transfer.Status.EXPIRED: "#6b7280",
        }

        color = colors.get(obj.status, "#6b7280")

        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Files")
    def file_count(self, obj):
        return obj.files.count()

    @admin.display(description="Expiry")
    def expiry_status(self, obj):
        if not obj.expires_at:
            return "Not started"

        if obj.expires_at <= timezone.now():
            return "Expired"

        return f"In {timesince(obj.expires_at)}"


@admin.register(TransferFile)
class TransferFileAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "transfer",
        "status",
        "size_bytes",
        "download_count",
        "max_downloads",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "original_filename",
        "object_key",
        "transfer__share_code",
    )

    readonly_fields = (
        "id",
        "transfer",
        "original_filename",
        "object_key",
        "declared_content_type",
        "content_type",
        "expected_size_bytes",
        "size_bytes",
        "status",
        "max_downloads",
        "download_count",
        "uploaded_at",
        "scanned_at",
        "created_at",
    )

    list_select_related = ("transfer",)
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False
