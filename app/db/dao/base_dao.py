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

    async def get_by_uuid(self, _uuid: Any, raise_not_found: bool = False) -> Optional[ModelT]:
        """Fetch a model instance by its UUID."""
        db_obj = await self.session.get(self.model, _uuid)
        if not db_obj and raise_not_found:
            if self.not_found_exc:
                raise self.not_found_exc(resource_name=self.model.__name__, identifier=_uuid)
            raise ValueError(f"{self.model.__name__} with uuid {_uuid} not found.")
        return db_obj

    async def get(self, **kwargs) -> list[ModelT]:
        """Fetch a list of model instances based on keyword arguments."""
        stmt = select(self.model)
        stmt = self._apply_filters(stmt, **kwargs)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj_in: PydanticBaseModel, should_commit: bool = True) -> ModelT:
        """Create a new model instance."""
        data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**data)

        self.session.add(db_obj)
        await self.session.flush()
        if should_commit:
            await self.session.commit()
        return db_obj

    async def update(self, db_obj: ModelT, obj_in: PydanticBaseModel, should_commit: bool = True) -> ModelT:
        """Update an existing model instance."""
        data = obj_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await self.session.flush()
        await self.session.refresh(db_obj)
        if should_commit:
            await self.session.commit()
        return db_obj

    async def update_by_uuid(self, obj_uuid: Any, should_commit: bool = True, **payload: Any) -> ModelT:
        """Update a model instance by its UUID."""
        obj = await self.get_by_uuid(obj_uuid, raise_not_found=True)

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
            if should_commit:
                await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return obj

    async def delete(self, _uuid: Any, should_commit: bool = True) -> Optional[ModelT]:
        """Delete a model instance by its UUID."""
        db_obj = await self.session.get(self.model, _uuid)
        if not db_obj:
            return None
        await self.session.delete(db_obj)
        await self.session.flush()
        if should_commit:
            await self.session.commit()
        return db_obj

    def _apply_filters(self, stmt, **kwargs):
        """
        Apply filters to the SQLAlchemy statement.

        Based on provided keyword arguments and additional filter expressions.
        Args:
            stmt: The SQLAlchemy select statement to which filters will be applied.
            filters: Optional list of additional filter expressions to apply.
            kwargs: Dictionary of field names and values to filter by, where keys
                    can include operators like 'eq', 'in', 'like', etc.
        Returns:
            The modified SQLAlchemy statement with applied filters.
        """
        for key, value in kwargs.items():
            if "__" in key:
                field_name, operator = key.split("__", 1)
            else:
                field_name, operator = key, "eq"

            if not hasattr(self.model, field_name):
                continue  # skip unknown fields

            column = getattr(self.model, field_name)

            if operator == "eq":
                stmt = stmt.where(column == value)
            elif operator == "in":
                stmt = stmt.where(column.in_(value))
            elif operator == "like":
                stmt = stmt.where(column.like(value))
            elif operator == "ilike":
                stmt = stmt.where(column.ilike(value))
            elif operator == "gt":
                stmt = stmt.where(column > value)
            elif operator == "gte":
                stmt = stmt.where(column >= value)
            elif operator == "lt":
                stmt = stmt.where(column < value)
            elif operator == "lte":
                stmt = stmt.where(column <= value)
            else:
                raise ValueError(f"Unsupported filter operator: {operator}")
        return stmt
