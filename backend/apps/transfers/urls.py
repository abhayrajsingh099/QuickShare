from django.urls import path

from .views import (
    HealthCheckView,
    TransferInitializationView,
    TransferCompletionView,
    TransferLookupView,
    FileDownloadView,
    TransferStatusView,
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
    path("lookup/", TransferLookupView.as_view(), name="lookup"),
    path(
        "<uuid:transfer_id>/files/<uuid:file_id>/download/",
        FileDownloadView.as_view(),
        name="file-download",
    ),
    path(
        "<uuid:transfer_id>/status/",
        TransferStatusView.as_view(),
        name="transfer-status",
    ),
    path("health/", HealthCheckView.as_view(), name="health-check"),
]