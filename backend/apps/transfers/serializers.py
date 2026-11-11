from django.conf import settings
from rest_framework import serializers


class TransferFileMetadataSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    size = serializers.IntegerField(min_value=1)
    content_type = serializers.CharField(max_length=255)


class TransferInitializationSerializer(serializers.Serializer):
    files = TransferFileMetadataSerializer(
        many=True,
        allow_empty=False,
    )

    def validate_files(self, files):
        max_files = settings.QUICKSHARE_MAX_FILES_PER_TRANSFER
        max_total_size = settings.QUICKSHARE_MAX_TRANSFER_SIZE_BYTES

        if len(files) > max_files:
            raise serializers.ValidationError(
                f"A maximum of {max_files} files is allowed per transfer."
            )

        total_size = sum(file["size"] for file in files)

        if total_size > max_total_size:
            raise serializers.ValidationError(
                "The total file size exceeds the 150 MiB transfer limit."
            )

        return files


class TransferLookupSerializer(serializers.Serializer):
    share_code = serializers.RegexField(
        regex=r"^\d{8}$",
        error_messages={
            "invalid": "Share code must contain exactly 8 digits."
        },
    )