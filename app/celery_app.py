from celery import Celery
from app.config import settings

celery_app=Celery(
    "recon_pipline",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.recon"]
    )

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    )
