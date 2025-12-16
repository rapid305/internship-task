from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.models import BaseModelMixin

ModelT = TypeVar("ModelT", bound=BaseModelMixin)


class BaseDAO(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_uuid(self, uuid: UUID) -> ModelT | None:
        stmt = select(self.model).where(self.model.uuid == uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, uuid: UUID, **values) -> None:
        stmt = update(self.model).where(self.model.uuid == uuid).values(**values)
        await self.session.execute(stmt)
        await self.session.commit()
