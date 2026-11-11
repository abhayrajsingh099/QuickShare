from pathlib import Path

from django.db import transaction
from django.utils import timezone
from django.db.models import Q

from apps.transfers.models import Transfer, TransferFile
from apps.transfers.services.s3 import S3StorageService


class TransferCleanupService:
    def cleanup_expired_transfers(self) -> int:
        now = timezone.now()

        expired_ids = list(
            Transfer.objects.filter(
                Q(
                    status=Transfer.Status.PENDING_UPLOAD,
                    upload_deadline_at__lte=now,
                )
                | Q(
                    status=Transfer.Status.ACTIVE,
                    expires_at__lte=now,
                )
                | Q(status=Transfer.Status.EXPIRED),
                files__storage_deleted_at__isnull=True,
            )
            .distinct()
            .values_list("id", flat=True)
        )

        active_expired_ids = Transfer.objects.filter(
            status=Transfer.Status.ACTIVE,
            expires_at__lte=now,
        ).values_list("id", flat=True)

        expired_ids.extend(active_expired_ids)

        cleaned_count = 0

        for transfer_id in expired_ids:
            if self.cleanup_transfer(transfer_id):
                cleaned_count += 1

        return cleaned_count

    def cleanup_transfer(self, transfer_id) -> bool:
        with transaction.atomic():
            transfer = (
                Transfer.objects.select_for_update()
                .filter(id=transfer_id)
                .first()
            )

            if transfer is None:
                return False

            now = timezone.now()

            if transfer.status == Transfer.Status.PENDING_UPLOAD:
                if transfer.upload_deadline_at > now:
                    return False

            elif transfer.status == Transfer.Status.ACTIVE:
                if transfer.expires_at is None or transfer.expires_at > now:
                    return False

            elif transfer.status == Transfer.Status.EXPIRED:
                pass

            else:
                return False

            transfer.status = Transfer.Status.EXPIRED
            transfer.save(update_fields=["status"])

        files = TransferFile.objects.filter(
            transfer_id=transfer_id,
            storage_deleted_at__isnull=True,
        )

        storage = S3StorageService()

        for file in files.iterator():
            try:
                storage.delete_object(file.object_key)

            except Exception:
                # Leave storage_deleted_at NULL.
                # A future cleanup run will retry this file.
                continue

            TransferFile.objects.filter(
                id=file.id,
                storage_deleted_at__isnull=True,
            ).update(storage_deleted_at=timezone.now())

        return True

    def cleanup_rejected_files(self) -> int:
        files = TransferFile.objects.filter(
            status=TransferFile.Status.REJECTED,
            storage_deleted_at__isnull=True,
        )

        storage = S3StorageService()
        deleted_count = 0

        for file in files.iterator():
            try:
                storage.delete_object(file.object_key)

            except Exception:
                # Leave the timestamp NULL for the next retry.
                continue

            updated = TransferFile.objects.filter(
                id=file.id,
                status=TransferFile.Status.REJECTED,
                storage_deleted_at__isnull=True,
            ).update(storage_deleted_at=timezone.now())

            deleted_count += updated

        return deleted_count

    def cleanup_temporary_scan_files(self, max_age_hours: int = 2) -> int:
        scan_directory = Path("/var/quickshare/scans")

        if not scan_directory.exists():
            return 0

        cutoff = timezone.now().timestamp() - (max_age_hours * 3600)
        deleted_count = 0

        for file_path in scan_directory.iterdir():
            if not file_path.is_file():
                continue

            try:
                if file_path.stat().st_mtime >= cutoff:
                    continue

                file_path.unlink()
                deleted_count += 1

            except OSError:
                # Leave it for the next cleanup run.
                continue

        return deleted_count
