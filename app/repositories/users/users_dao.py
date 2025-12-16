from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import User


class UsersDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        user_uuid: UUID | None = None,
        email: str | None = None,
        status: str | None = None,
    ) -> Sequence[User]:
        stmt = select(User).options(selectinload(User.user_balance)).order_by(User.created.desc())

        if user_uuid is not None:
            stmt = stmt.where(User.uuid == user_uuid)
        if email is not None:
            stmt = stmt.where(User.email == email)
        if status is not None:
            stmt = stmt.where(User.status == status)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_uuid(self, user_uuid: UUID) -> User | None:
        result = await self.session.execute(
            select(User).options(selectinload(User.user_balance)).where(User.uuid == user_uuid)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        return user

    async def update_status(self, user_uuid: UUID, status: str) -> None:
        await self.session.execute(update(User).where(User.uuid == user_uuid).values(status=status))
        await self.session.commit()
