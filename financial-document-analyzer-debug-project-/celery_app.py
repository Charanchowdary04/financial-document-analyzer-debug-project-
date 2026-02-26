"""Celery app and analysis task for background processing."""
from celery import Celery
from config import CELERY_BROKER_URL

celery_app = Celery(
    "financial_analyzer",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL,
    include=["celery_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_track_started=True,
)
