import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging_conf import get_logger

logger = get_logger(__name__)

_redis_client: aioredis.Redis | None = None  # type: ignore[type-arg]


async def get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def redis_set(key: str, value: Any, ttl: int | None = None) -> None:
    client = await get_redis()
    serialized = json.dumps(value, default=str)
    if ttl:
        await client.setex(key, ttl, serialized)
    else:
        await client.set(key, serialized)


async def redis_get(key: str) -> Any | None:
    client = await get_redis()
    data = await client.get(key)
    return json.loads(data) if data else None


async def redis_delete(key: str) -> None:
    client = await get_redis()
    await client.delete(key)


async def redis_delete_pattern(pattern: str) -> int:
    client = await get_redis()
    keys = await client.keys(pattern)
    if keys:
        return await client.delete(*keys)
    return 0


async def redis_ping() -> bool:
    try:
        client = await get_redis()
        return bool(await client.ping())
    except Exception:
        return False
