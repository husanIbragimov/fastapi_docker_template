import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings
from app.core.exceptions import InvalidTokenException


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    expire = _now_utc() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject,
        "jti": str(uuid.uuid4()),
        "type": "access",
        "iat": _now_utc(),
        "exp": expire,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> tuple[str, str]:
    """Returns (token, jti). jti is stored in Redis for rotation tracking."""
    jti = str(uuid.uuid4())
    expire = _now_utc() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload: dict[str, Any] = {
        "sub": subject,
        "jti": jti,
        "type": "refresh",
        "iat": _now_utc(),
        "exp": expire,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise InvalidTokenException("Token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenException("Token is invalid")
