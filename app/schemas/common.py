from typing import Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    success: bool = True
    message: str = "Success"
    data: DataT | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str
    details: list | None = None


class PaginationMeta(BaseModel):
    page: int
    size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[DataT]):
    success: bool = True
    message: str = "Success"
    data: list[DataT]
    meta: PaginationMeta
