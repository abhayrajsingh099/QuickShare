import hashlib
import secrets
from datetime import timedelta
from uuid import uuid4

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.transfers.models import Transfer, TransferFile
from apps.transfers.services.s3 import S3StorageService


UPLOAD_POST_EXPIRES_IN = 300
SHARE_CODE_ATTEMPTS = 5


class TransferService:
    def __init__(self):
        self.s3_service = S3StorageService()

    @transaction.atomic
    def initialize_transfer(self, files_metadata: list[dict]) -> dict:
        upload_deadline = timezone.now() + timedelta(
            seconds=UPLOAD_POST_EXPIRES_IN
        )

        # Generate a unique sharing code.
        for attempt in range(SHARE_CODE_ATTEMPTS):
            share_code = f"{secrets.randbelow(100_000_000):08d}"

            try:
                with transaction.atomic():
                    transfer = Transfer.objects.create(
                        share_code=share_code,
                        upload_deadline_at=upload_deadline,
                    )
                break
            except IntegrityError:
                if attempt == SHARE_CODE_ATTEMPTS - 1:
                    raise

        upload_token = secrets.token_urlsafe(32)

        transfer.upload_token_hash = hashlib.sha256(
            upload_token.encode()
        ).hexdigest()

        transfer.save(update_fields=["upload_token_hash"])

        upload_instructions = []

        for metadata in files_metadata:
            file_id = uuid4()

            object_key = (
                f"quarantine/{transfer.id}/{file_id}"
            )

            transfer_file = TransferFile.objects.create(
                id=file_id,
                transfer=transfer,
                original_filename=metadata["filename"],
                object_key=object_key,
                declared_content_type=metadata["content_type"],
                expected_size_bytes=metadata["size"],
            )

            upload_post = self.s3_service.generate_upload_post(
                object_key=object_key,
                max_size_bytes=transfer_file.expected_size_bytes,
                expires_in=UPLOAD_POST_EXPIRES_IN,
            )

            upload_instructions.append({
                "file_id": str(transfer_file.id),
                "filename": transfer_file.original_filename,
                "upload_url": upload_post["url"],
                "upload_fields": upload_post["fields"],
            })

        return {
            "transfer_id": str(transfer.id),
            "share_code": transfer.share_code,
            "upload_token": upload_token,
            "upload_deadline_at": upload_deadline.isoformat(),
            "files": upload_instructions,
        }