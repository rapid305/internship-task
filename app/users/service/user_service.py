from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestDataException
from app.core.schemas import CurrencyEnum
from app.outbox.outbox_service import OutboxService
from app.users.dao.users_dao import UsersDAO
from app.users.exceptions import (
    UserAlreadyActiveException,
    UserAlreadyBlockedException,
    UserAlreadyExistsException,
    UserNotExistsException,
)
from app.users.schemas import (
    CreateUserModel,
    RequestUserModel,
    ResponseUserBalanceModel,
    ResponseUserModel,
    UserFilters,
    UserModel,
    UserStatusEnum,
)


class UserService:
    def __init__(self, session: AsyncSession, outbox_service: OutboxService):
        self.session = session
        self.user_dao = UsersDAO(session)
        self.outbox_service = outbox_service

    async def get_users(
        self,
        filters: Optional[UserFilters] = None,
    ) -> list[ResponseUserModel]:
        users = await self.user_dao.get_all_with_balances(filters=filters)
        return [ResponseUserModel.model_validate(user) for user in users]

    async def create_user(self, user: RequestUserModel) -> ResponseUserModel:
        normalized_email = user.email
        if not normalized_email:
            raise BadRequestDataException()

        if await self.user_dao.get_by_email(normalized_email):
            raise UserAlreadyExistsException()

        balances = [ResponseUserBalanceModel(currency=currency, amount=Decimal(0)) for currency in CurrencyEnum]

        user_data = CreateUserModel(
            email=normalized_email,
            status=UserStatusEnum.ACTIVE,
            user_balance=balances,
        )

        created_user = await self.user_dao.create_user_with_balance(user_data)

        await self.outbox_service.add_event(
            aggregate_id=str(created_user.uuid),
            event_type="USER_CREATED",
            payload={
                "event_type": "USER_CREATED",
                "user_id": str(created_user.uuid),
                "email": created_user.email,
                "status": created_user.status,
            },
        )

        await self.session.commit()

        return ResponseUserModel.model_validate(created_user)

    async def change_status(self, user_uuid: UUID, new_status: UserStatusEnum) -> UserModel:
        user = await self.user_dao.get_by_uuid(user_uuid)
        if not user:
            raise UserNotExistsException()

        status_str = new_status
        if user.status == status_str:
            if new_status == UserStatusEnum.ACTIVE:
                raise UserAlreadyActiveException()
            raise UserAlreadyBlockedException()

        old_status = user.status
        changed_user = await self.user_dao.update_status(user_uuid, status_str)

        await self.outbox_service.add_event(
            aggregate_id=str(user_uuid),
            event_type="USER_STATUS_CHANGED",
            payload={
                "event_type": "USER_STATUS_CHANGED",
                "user_id": str(user_uuid),
                "old_status": old_status,
                "new_status": status_str,
                "email": user.email,
            },
        )

        await self.session.commit()

        return UserModel.model_validate(changed_user)
