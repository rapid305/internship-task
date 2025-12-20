from typing import Any, Generic, Optional, Type, TypeVar

from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.exceptions import DaoAttributeError, DaoNotFoundError
from app.core.models import BaseModelMixin

ModelT = TypeVar("ModelT", bound=BaseModelMixin)


class BaseDAO(Generic[ModelT]):
    model: Type[ModelT]
    not_found_exc: Type[DaoNotFoundError] = DaoNotFoundError
    attribute_error_exc: Type[DaoAttributeError] = DaoAttributeError

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_uuid(self, _uuid: Any) -> Optional[ModelT]:
        """Fetch a model instance by its UUID."""
        db_obj = await self.session.get(self.model, _uuid)
        if not db_obj:
            if self.not_found_exc:
                raise self.not_found_exc(resource_name=self.model.__name__, identifier=_uuid)
            raise ValueError(f"{self.model.__name__} with id {_uuid} not found.")
        return db_obj

    async def get(
        self,
    ) -> list[ModelT]:
        """Fetch a list of model instances"""
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj_in: PydanticBaseModel) -> ModelT:
        """Create a new model instance."""
        data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**data)

        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelT, obj_in: PydanticBaseModel) -> ModelT:
        """Update an existing model instance."""
        data = obj_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update_by_uuid(self, obj_uuid: Any, **payload: Any) -> ModelT:
        """Update a model instance by its UUID."""
        obj = await self.get_by_uuid(obj_uuid)

        for key, value in payload.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
            else:
                if self.attribute_error_exc:
                    raise self.attribute_error_exc(self.model.__name__, key)
                raise AttributeError(f"'{self.model.__name__}' object has no attribute '{key}'")

        try:
            await self.session.flush()
            await self.session.refresh(obj)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return obj

    async def delete(self, _uuid: Any) -> Optional[ModelT]:
        """Delete a model instance by its UUID."""
        db_obj = await self.session.get(self.model, _uuid)
        if not db_obj:
            return None
        await self.session.delete(db_obj)
        await self.session.flush()
        return db_obj
