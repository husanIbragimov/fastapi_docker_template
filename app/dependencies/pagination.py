from fastapi import Query

from app.utils.pagination import PaginationParams


def pagination_params(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    return PaginationParams(page=page, size=size)
