from django.db import DatabaseError, connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


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