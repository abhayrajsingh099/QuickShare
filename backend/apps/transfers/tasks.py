from celery import shared_task


@shared_task
def test_background_task(file_id: str):
    print(f"QuickShare: Processing file {file_id}")


def enqueue_file_scan_tasks(file_ids: list[str]) -> None:
    for file_id in file_ids:
        test_background_task.delay(file_id)