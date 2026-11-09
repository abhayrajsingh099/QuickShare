from django.db import DatabaseError, connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.transfers.serializers import TransferInitializationSerializer
from apps.transfers.services.transfers import TransferService


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