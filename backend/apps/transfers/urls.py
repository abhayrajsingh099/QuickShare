from django.urls import path

from .views import (
    HealthCheckView,
    TransferInitializationView,
    TransferCompletionView,
)

urlpatterns = [
    path(
            "",
            TransferInitializationView.as_view(),
            name="initialize",
        ),
    path(
        "<uuid:transfer_id>/complete/",
        TransferCompletionView.as_view(),
        name="complete",
    ),
    path("health/", HealthCheckView.as_view(), name="health-check"),
]