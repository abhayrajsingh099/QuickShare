from django.utils import timezone
from celery import shared_task
from clamav_client import get_scanner

from pathlib import Path
from django.db import transaction
from django.conf import settings

from apps.transfers.services.s3 import S3StorageService
from apps.transfers.models import TransferFile

from apps.transfers.services.cleanup import TransferCleanupService


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def scan_transfer_file(self, file_id: str):
    try:
        # 1. Validate file state and download from S3.
        file_path = get_file_for_scanning(file_id)

        if file_path is None:
            return

        # 2. Scan with ClamAV.
        scan_result = scan_local_file(file_path)

        # 3. Save the result in PostgreSQL.
        save_scan_result(file_id, scan_result)

    except Exception as exc:
        raise self.retry(exc=exc)

def enqueue_file_scan_tasks(file_ids: list[str]) -> None:
    for file_id in file_ids:
        scan_transfer_file.delay(file_id)

def prepare_file_for_scanning(file_id: str):
    with transaction.atomic():
        file = (
            TransferFile.objects.select_for_update()
            .filter(id=file_id)
            .first()
        )

        if file is None:
            return None

        # Ignore files that have already reached a terminal state.
        if file.status in {
            TransferFile.Status.AVAILABLE,
            TransferFile.Status.REJECTED,
            TransferFile.Status.DELETED,
        }:
            return None

        # Only uploaded or previously interrupted scans can proceed.
        if file.status not in {
            TransferFile.Status.UPLOADED,
            TransferFile.Status.SCANNING,
        }:
            return None

        if file.status == TransferFile.Status.UPLOADED:
            file.status = TransferFile.Status.SCANNING
            file.save(update_fields=["status"])

        return file.object_key


def download_file_for_scanning(file_id: str, object_key: str) -> str:
    scan_directory = Path("/var/quickshare/scans")
    scan_directory.mkdir(parents=True, exist_ok=True)

    # Use UUID, never the user-provided filename.
    destination_path = scan_directory / file_id

    S3StorageService().download_object(
        object_key=object_key,
        destination_path=str(destination_path),
    )

    return str(destination_path)

def get_file_for_scanning(file_id: str) -> str | None:
    object_key = prepare_file_for_scanning(file_id)

    if object_key is None:
        return None

    return download_file_for_scanning(file_id, object_key)

def scan_local_file(file_path: str):
    scanner = get_scanner({
        "backend": "clamd",
        "address": f"{settings.CLAMAV_HOST}:{settings.CLAMAV_PORT}",
        "stream": False,
    })

    return scanner.scan(file_path)


def save_scan_result(file_id: str, scan_result) -> None:
    if scan_result.state == "OK":
        new_status = TransferFile.Status.AVAILABLE

    elif scan_result.state == "FOUND":
        new_status = TransferFile.Status.REJECTED

    else:
        # Scanner errors are operational failures, not malware detections.
        raise RuntimeError(
            f"ClamAV scan failed: "
            f"state={scan_result.state}, "
            f"details={scan_result.details}, "
            f"error={scan_result.err}"
        )

    with transaction.atomic():
        file = TransferFile.objects.select_for_update().get(id=file_id)

        # Don't overwrite a state changed by another process.
        if file.status != TransferFile.Status.SCANNING:
            return

        file.status = new_status
        file.scanned_at = timezone.now()

        file.save(update_fields=["status", "scanned_at"])



@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def cleanup_quickshare_storage(self):
    try:
        cleanup = TransferCleanupService()

        expired_transfers = cleanup.cleanup_expired_transfers()
        rejected_files = cleanup.cleanup_rejected_files()
        temporary_files = cleanup.cleanup_temporary_scan_files()

        return {
            "expired_transfers": expired_transfers,
            "rejected_files": rejected_files,
            "temporary_files": temporary_files,
        }

    except Exception as exc:
        raise self.retry(exc=exc)