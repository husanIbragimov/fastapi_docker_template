import math

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


def build_pagination_meta(*, page: int, size: int, total: int) -> PaginationMeta:
    total_pages = math.ceil(total / size) if size > 0 else 0
    return PaginationMeta(page=page, size=size, total=total, total_pages=total_pages)
