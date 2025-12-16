from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from app.repositories.users.user_repository import UserRepository
from app.db.models import User, UserBalance
from app.core.schemas import CurrencyEnum
from app.schemas.user_schemas import UserStatusEnum

from app.exceptions.common_exceptions import BadRequestDataException
from app.exceptions.user_exceptions import (
    UserAlreadyExistsException,
    UserNotExistsException,
    UserAlreadyActiveException,
    UserAlreadyBlockedException,
)
from app.schemas.user_schemas import RequestUserModel


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_users(self,
        user_uuid: UUID | None = None,
        email: str | None = None,
        status: str | None = None,
        ) -> Sequence[User]:
        return await self.user_repository.get_users(user_uuid=user_uuid, email=email, status=status)

    async def create_user(self, user: RequestUserModel) -> User:
        normalized_email = user.email.strip().replace(" ", "")
        if not normalized_email:
            raise BadRequestDataException()

        if await self.user_repository.get_by_email(normalized_email):
            raise UserAlreadyExistsException()

        user = User(
            email=normalized_email,
            status=UserStatusEnum.ACTIVE,
            created=datetime.now(timezone.utc),
            updated = datetime.now(timezone.utc),
            user_balance=[
                UserBalance(currency=str(currency.value), amount=0)
                for currency in CurrencyEnum
            ],
        )
        return await self.user_repository.add_user(user)

    async def change_status(self, user_uuid: UUID, new_status: UserStatusEnum) -> User:
        user = await self.user_repository.get_user(user_uuid)
        if not user:
            raise UserNotExistsException()

        if user.status == new_status.value:
            if new_status == UserStatusEnum.ACTIVE:
                raise UserAlreadyActiveException()
            raise UserAlreadyBlockedException()

        await self.user_repository.change_status(user_uuid, str(new_status.value))

        user.status = str(new_status.value)
        user.updated = datetime.now(timezone.utc)
        return user
