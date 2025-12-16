from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.dao.base_dao import BaseDAO
from app.db.models import User
from app.schemas.user_schemas import UserFilters


class UsersDAO(BaseDAO[User]):
    model = User

    async def get_all(self, filters: UserFilters) -> Sequence[User]:
        stmt = select(User).options(selectinload(User.user_balance)).order_by(User.created.desc())

        if filters.uuid is not None:
            stmt = stmt.where(User.uuid == filters.uuid)
        if filters.email is not None:
            stmt = stmt.where(User.email == filters.email)
        if filters.status is not None:
            stmt = stmt.where(User.status == filters.status)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj: User) -> User:
        await super().create(obj)

        stmt = select(User).where(User.uuid == obj.uuid).options(selectinload(User.user_balance))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def update_status(self, user_uuid: UUID, status: str) -> None:
        await self.update(user_uuid, status=status)
