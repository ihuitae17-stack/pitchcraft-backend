from celery import Celery
from app.config import get_settings

settings = get_settings()

# Celery 앱 생성
celery_app = Celery(
    "pitchcraft",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.analysis_tasks"]
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10분 타임아웃
    worker_prefetch_multiplier=1,  # CPU 집약적 작업
    worker_max_tasks_per_child=10,  # 메모리 누수 방지
)
