from django.db import DatabaseError, connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.transfers.serializers import TransferInitializationSerializer, TransferLookupSerializer
from apps.transfers.services.transfers import TransferService
from apps.transfers.services.receivers import ReceiverService

class HealthCheckView(APIView):

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

            return Response({
                "status": "ok",
                "database": "connected",
            })

        except DatabaseError:
            return Response(
                {
                    "status": "unhealthy",
                    "database": "disconnected",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

class TransferInitializationView(APIView):
    def post(self, request):
        serializer = TransferInitializationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transfer_data = TransferService().initialize_transfer(
            serializer.validated_data["files"]
        )

        return Response(
            transfer_data,
            status=status.HTTP_201_CREATED,
        )


class TransferCompletionView(APIView):
    def post(self, request, transfer_id):
        upload_token = request.headers.get("X-Upload-Token")

        if not upload_token:
            return Response(
                {"detail": "X-Upload-Token header is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = TransferService().complete_transfer(
            transfer_id=transfer_id,
            upload_token=upload_token,
        )

        return Response(result, status=status.HTTP_200_OK)

class TransferLookupView(APIView):
    def post(self, request):
        serializer = TransferLookupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = ReceiverService().lookup_transfer(
            share_code=serializer.validated_data["share_code"],
        )

        return Response(result, status=status.HTTP_200_OK)

class FileDownloadView(APIView):
    def post(self, request, transfer_id, file_id):
        result = ReceiverService().issue_download_url(
            transfer_id=transfer_id,
            file_id=file_id,
        )

        return Response(result, status=status.HTTP_200_OK)


class TransferStatusView(APIView):
    def get(self, request, transfer_id):
        upload_token = request.headers.get("X-Upload-Token")

        if not upload_token:
            return Response(
                {"detail": "X-Upload-Token header is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = TransferService().get_transfer_status(
            transfer_id=transfer_id,
            upload_token=upload_token,
        )

        return Response(result, status=status.HTTP_200_OK)