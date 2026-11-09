import boto3
from django.conf import settings


class S3StorageService:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION_NAME,
        )

    def generate_upload_post(
        self,
        object_key: str,
        max_size_bytes: int,
        expires_in: int = 300,
    ) -> dict:
        return self.client.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=object_key,
            Conditions=[
                ["content-length-range", 1, max_size_bytes],
            ],
            ExpiresIn=expires_in,
        )