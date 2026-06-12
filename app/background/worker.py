import asyncio
from typing import Any

from arq.connections import RedisSettings

from app.core.config import settings
from app.core.logging_conf import get_logger, setup_logging

logger = get_logger(__name__)


async def send_email_task(ctx: dict[str, Any], to: str, subject: str, body: str) -> None:
    """arq task: send an email. Retried automatically up to max_tries on failure."""
    logger.info("email_task_running", to=to, subject=subject)
    await asyncio.sleep(0)  # replace with real SMTP / SES / SendGrid call
    logger.info("email_task_done", to=to)


async def process_notification_task(
    ctx: dict[str, Any], user_id: str, event: str, payload: dict[str, Any]
) -> None:
    """arq task: process a user notification event."""
    logger.info("notification_task", user_id=user_id, event=event)
    await asyncio.sleep(0)  # replace with real notification logic
    logger.info("notification_task_done", user_id=user_id)


async def generate_report_task(
    ctx: dict[str, Any], report_type: str, params: dict[str, Any]
) -> None:
    """arq task: generate a background report."""
    logger.info("report_task", report_type=report_type)
    await asyncio.sleep(0)  # replace with real report generation
    logger.info("report_task_done", report_type=report_type)


async def startup(ctx: dict[str, Any]) -> None:
    setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    logger.info("arq_worker_started")


async def shutdown(ctx: dict[str, Any]) -> None:
    logger.info("arq_worker_stopped")


class WorkerSettings:
    functions = [send_email_task, process_notification_task, generate_report_task]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    retry_jobs = True
    max_tries = 3
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
    )
