from abc import ABC, abstractmethod
from typing import Optional, Sequence
from uuid import UUID

from app.db.models import User


class IUserRepository(ABC):

    @abstractmethod
    async def get_users(
        self,
        user_uuid: Optional[UUID] = None,
        email: Optional[str] = None,
        status: str | None = None,
    ) -> Sequence[User]: ...

    @abstractmethod
    async def get_user(self, user_uuid: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def change_status(self, user_uuid: UUID, status: str) -> None: ...

    @abstractmethod
    async def add_user(self, user: User) -> User: ...
