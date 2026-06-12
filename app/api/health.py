from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.backend import redis_ping
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict:
    return {"status": "ok", "service": "fastapi-template"}


@router.get("/db")
async def db_health(session: AsyncSession = Depends(get_db)) -> JSONResponse:
    try:
        await session.execute(text("SELECT 1"))
        return JSONResponse({"status": "ok", "database": "connected"})
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": str(exc)},
        )


@router.get("/redis")
async def redis_health() -> JSONResponse:
    ok = await redis_ping()
    if ok:
        return JSONResponse({"status": "ok", "redis": "connected"})
    return JSONResponse(
        status_code=503, content={"status": "error", "redis": "unreachable"}
    )
