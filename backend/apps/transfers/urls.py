from django.urls import path

from .views import (
    HealthCheckView,
    TransferInitializationView,
)

urlpatterns = [
    path(
            "",
            TransferInitializationView.as_view(),
            name="initialize",
        ),
    path("health/", HealthCheckView.as_view(), name="health-check"),
]