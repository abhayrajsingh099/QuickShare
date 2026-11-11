import hashlib
import secrets
from datetime import timedelta
from uuid import uuid4
from functools import partial
from apps.transfers.tasks import enqueue_file_scan_tasks

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from rest_framework.exceptions import ValidationError

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


    def complete_transfer(
        self,
        transfer_id: str,
        upload_token: str,
    ) -> dict:
        # 1. Retrieve the transfer.
        transfer = get_object_or_404(Transfer, id=transfer_id)

        # 2. Authenticate the sender.
        expected_hash = transfer.upload_token_hash or ""
        actual_hash = hashlib.sha256(upload_token.encode()).hexdigest()

        if not secrets.compare_digest(expected_hash, actual_hash):
            raise PermissionDenied("Invalid upload token.")

        # 3. Handle repeated completion requests.
        if transfer.status == Transfer.Status.ACTIVE:
            return {
                "status": transfer.status,
                "already_completed": True,
                "expires_at": transfer.expires_at.isoformat(),
            }

        if transfer.status != Transfer.Status.PENDING_UPLOAD:
            raise ValidationError("This transfer cannot be completed.")

        # 4. Check upload deadline.
        if timezone.now() >= transfer.upload_deadline_at:
            Transfer.objects.filter(
                id=transfer.id,
                status=Transfer.Status.PENDING_UPLOAD,
            ).update(status=Transfer.Status.EXPIRED)

            raise ValidationError("The upload deadline has expired.")

        # 5. Verify all expected S3 objects.
        files = list(transfer.files.all())

        if not files:
            raise ValidationError("No files found for this transfer.")

        verification_errors = []
        verified_sizes = {}

        for file in files:
            actual_size = self.s3_service.get_object_size(file.object_key)

            if actual_size is None:
                verification_errors.append({
                    "file_id": str(file.id),
                    "filename": file.original_filename,
                    "reason": "File is missing from S3.",
                })
            elif actual_size != file.expected_size_bytes:
                verification_errors.append({
                    "file_id": str(file.id),
                    "filename": file.original_filename,
                    "reason": "File size does not match.",
                })
            else:
                verified_sizes[file.id] = actual_size

        if verification_errors:
            raise ValidationError({"files": verification_errors})

        # 6. Finalize the transfer atomically.
        with transaction.atomic():
            locked_transfer = Transfer.objects.select_for_update().get(
                id=transfer.id
            )

            # Another request may have completed it meanwhile.
            if locked_transfer.status == Transfer.Status.ACTIVE:
                return {
                    "status": locked_transfer.status,
                    "already_completed": True,
                    "expires_at": locked_transfer.expires_at.isoformat(),
                }

            if (
                locked_transfer.status != Transfer.Status.PENDING_UPLOAD
                or timezone.now() >= locked_transfer.upload_deadline_at
            ):
                raise ValidationError(
                    "The transfer can no longer be completed."
                )

            completion_time = timezone.now()

            updated_count = locked_transfer.files.filter(
                status=TransferFile.Status.PENDING_UPLOAD,
            ).update(
                status=TransferFile.Status.UPLOADED,
                uploaded_at=completion_time,
            )

            if updated_count != len(files):
                raise ValidationError(
                    "The file states changed during completion."
                )

            for file in files:
                file.size_bytes = verified_sizes[file.id]

            TransferFile.objects.bulk_update(files, ["size_bytes"])

            locked_transfer.status = Transfer.Status.ACTIVE
            locked_transfer.upload_completed_at = completion_time
            locked_transfer.expires_at = (
                completion_time
                + timedelta(
                    seconds=settings.QUICKSHARE_TRANSFER_TTL_SECONDS
                )
            )

            locked_transfer.save(
                update_fields=[
                    "status",
                    "upload_completed_at",
                    "expires_at",
                ]
            )

            file_ids = [str(file.id) for file in files]

            transaction.on_commit(
                partial(enqueue_file_scan_tasks, file_ids)
            )

        return {
            "status": Transfer.Status.ACTIVE,
            "already_completed": False,
            "expires_at": locked_transfer.expires_at.isoformat(),
        }
