from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.dao.base_dao import BaseDAO
from app.db.models import User, UserBalance
from app.schemas.user_schemas import CreateUserModel, UserFilters


class UsersDAO(BaseDAO[User]):
    model = User

    async def get_all(self, filters: Optional[UserFilters] = None) -> Sequence[User]:
        stmt = select(self.model)
        if filters:
            stmt = self._apply_filters(stmt, kwargs=filters.model_dump(exclude_none=True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_with_balances(self, filters: Optional[UserFilters] = None) -> Sequence[User]:
        stmt = select(self.model).options(selectinload(User.user_balance))
        if filters:
            stmt = self._apply_filters(stmt, kwargs=filters.model_dump(exclude_none=True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_status(self, user_uuid: UUID, status: str) -> User:
        return await self.update_by_uuid(user_uuid, status=status)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user_with_balance(self, obj: CreateUserModel) -> User:
        user = User(
            email=obj.email,
            status=obj.status,
        )

        user.user_balance = [UserBalance(currency=b.currency, amount=b.amount) for b in obj.user_balance]

        self.session.add(user)
        await self.session.flush()

        stmt = select(User).options(selectinload(User.user_balance)).where(User.uuid == user.uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one()
