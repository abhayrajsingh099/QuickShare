from celery import shared_task


@shared_task
def test_background_task():
    print("QuickShare: Background task executed!")
    return "Success"