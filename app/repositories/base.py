import uuid
from typing import Any, Generic, Type, TypeVar

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> list[ModelType]:
        result = await self.session.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def create(self, **kwargs: Any) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update_by_id(self, id: uuid.UUID, **kwargs: Any) -> ModelType | None:
        kwargs_clean = {k: v for k, v in kwargs.items() if v is not None}
        if not kwargs_clean:
            return await self.get_by_id(id)
        await self.session.execute(
            update(self.model)  # type: ignore[arg-type]
            .where(self.model.id == id)  # type: ignore[attr-defined]
            .values(**kwargs_clean)
        )
        await self.session.flush()
        return await self.get_by_id(id)

    async def delete_by_id(self, id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        )
        return result.rowcount > 0  # type: ignore[return-value]
