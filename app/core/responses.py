from typing import Any

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import AppException
from app.core.logging_conf import get_logger

logger = get_logger(__name__)


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": jsonable_encoder(data)},
    )


def error_response(
    message: str,
    error_code: str = "ERROR",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Any = None,
) -> JSONResponse:
    body: dict[str, Any] = {"success": False, "message": message, "error_code": error_code}
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        "app_exception",
        path=request.url.path,
        error_code=exc.error_code,
        message=exc.message,
    )
    return error_response(exc.message, exc.error_code, exc.status_code)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning("validation_error", path=request.url.path, errors=exc.errors())
    return error_response(
        message="Validation failed",
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        details=exc.errors(),
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error("database_error", path=request.url.path, error=str(exc))
    return error_response(
        message="A database error occurred",
        error_code="DATABASE_ERROR",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", path=request.url.path, error=str(exc))
    return error_response(
        message="An unexpected error occurred",
        error_code="INTERNAL_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
