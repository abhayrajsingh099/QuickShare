from django.utils import timezone
from django.db import transaction

from rest_framework.exceptions import NotFound, PermissionDenied

from apps.transfers.models import Transfer, TransferFile
from apps.transfers.services.s3 import S3StorageService

class ReceiverService:
    def lookup_transfer(self, share_code: str) -> dict:
        transfer = Transfer.objects.filter(
            share_code=share_code,
            status=Transfer.Status.ACTIVE,
            expires_at__gt=timezone.now(),
        ).first()

        if transfer is None:
            raise NotFound("Transfer not found or expired.")

        available_files = transfer.files.filter(
            status=TransferFile.Status.AVAILABLE,
        ).values(
            "id",
            "original_filename",
            "size_bytes",
            "declared_content_type",
        )

        return {
            "transfer_id": str(transfer.id),
            "expires_at": transfer.expires_at,
            "files": list(available_files),
        }

    def issue_download_url(
        self,
        transfer_id: str,
        file_id: str,
    ) -> dict:
        with transaction.atomic():
            transfer = (
                Transfer.objects.select_for_update()
                .filter(
                    id=transfer_id,
                    status=Transfer.Status.ACTIVE,
                    expires_at__gt=timezone.now(),
                )
                .first()
            )

            if transfer is None:
                raise NotFound("Transfer not found or expired.")

            file = (
                TransferFile.objects.select_for_update()
                .filter(
                    id=file_id,
                    transfer=transfer,
                    status=TransferFile.Status.AVAILABLE,
                )
                .first()
            )

            if file is None:
                raise NotFound("File not found or unavailable.")

            if file.download_count >= file.max_downloads:
                raise PermissionDenied("Download limit reached.")

            download_url = S3StorageService().generate_download_url(
                object_key=file.object_key,
                expires_in=60,
            )

            file.download_count += 1
            file.save(update_fields=["download_count"])

            return {
                "download_url": download_url,
                "expires_in": 60,
                "downloads_remaining": file.max_downloads - file.download_count,
            }