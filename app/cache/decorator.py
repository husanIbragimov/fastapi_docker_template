import hashlib
import json
from collections.abc import Callable
from functools import wraps
from typing import Any

from app.cache.backend import get_redis
from app.core.logging_conf import get_logger

logger = get_logger(__name__)


def _build_cache_key(func: Callable, namespace: str, args: tuple, kwargs: dict) -> str:
    ns = namespace or f"{func.__module__}.{func.__qualname__}"
    raw = json.dumps({"args": list(args[1:]), "kwargs": kwargs}, default=str, sort_keys=True)
    digest = hashlib.md5(raw.encode()).hexdigest()  # noqa: S324
    return f"cache:{ns}:{digest}"


def cache(ttl: int = 300, namespace: str = "") -> Callable:
    """
    Decorator for async methods/functions. Caches return value in Redis.

    Usage::

        @cache(ttl=300, namespace="users")
        async def get_user_list(self, page: int, size: int) -> dict:
            ...

    Attach ``.invalidate(*same_args)`` to clear a specific cached entry.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                redis = await get_redis()
                key = _build_cache_key(func, namespace, args, kwargs)

                cached = await redis.get(key)
                if cached:
                    return json.loads(cached)

                result = await func(*args, **kwargs)
                await redis.set(key, json.dumps(result, default=str), ex=ttl)
                return result
            except Exception as exc:
                logger.warning("cache_error", func=func.__qualname__, error=str(exc))
                return await func(*args, **kwargs)

        async def invalidate(*args: Any, **kwargs: Any) -> None:
            try:
                redis = await get_redis()
                key = _build_cache_key(func, namespace, args, kwargs)
                await redis.delete(key)
            except Exception:
                pass

        wrapper.invalidate = invalidate  # type: ignore[attr-defined]
        return wrapper

    return decorator
