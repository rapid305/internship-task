from typing import Sequence
from uuid import UUID

from app.db.models import User
from app.repositories.users.user_repository_interface import IUserRepository
from app.repositories.users.users_dao import UsersDAO


class UserRepository(IUserRepository):
    def __init__(self, dao: UsersDAO):
        self.dao = dao

    async def get_users(
        self,
        user_uuid: UUID | None = None,
        email: str | None = None,
        status: str | None = None,
    ) -> Sequence[User]:
        return await self.dao.get_all(
            user_uuid=user_uuid,
            email=email,
            status=status,
        )

    async def get_user(self, user_uuid: UUID) -> User | None:
        return await self.dao.get_by_uuid(user_uuid)

    async def get_by_email(self, email: str) -> User | None:
        return await self.dao.get_by_email(email)

    async def add_user(self, user: User) -> User:
        return await self.dao.create(user)

    async def change_status(self, user_uuid: UUID, status: str) -> None:
        await self.dao.update_status(user_uuid, status)
