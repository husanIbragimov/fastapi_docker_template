import asyncio

from app.core.logging_conf import get_logger

logger = get_logger(__name__)


async def send_welcome_email(email: str, username: str) -> None:
    """FastAPI BackgroundTask: queued after registration, runs in the same process."""
    await asyncio.sleep(0)  # yield to event loop; replace with real SMTP/SES call
    logger.info("welcome_email_sent", email=email, username=username)
