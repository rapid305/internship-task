from uuid import UUID

from app.core.schemas import CurrencyEnum
from app.db.dao.users_dao import UsersDAO
from app.db.models import User, UserBalance
from app.exceptions.common_exceptions import BadRequestDataException
from app.exceptions.user_exceptions import (
    UserAlreadyActiveException,
    UserAlreadyBlockedException,
    UserAlreadyExistsException,
    UserNotExistsException,
)
from app.schemas.user_schemas import RequestUserModel, ResponseUserModel, UserFilters, UserStatusEnum


class UserService:
    def __init__(self, user_dao: UsersDAO):
        self.user_dao = user_dao

    async def get_users(
        self,
        filters: UserFilters,
    ) -> list[ResponseUserModel]:
        users = await self.user_dao.get_all(
            filters=filters,
        )
        return [ResponseUserModel.model_validate(user) for user in users]

    async def create_user(self, user: RequestUserModel) -> ResponseUserModel:
        normalized_email = user.email
        if not normalized_email:
            raise BadRequestDataException()

        if await self.user_dao.get_by_email(normalized_email):
            raise UserAlreadyExistsException()

        user_orm = User(
            email=normalized_email,
            status=UserStatusEnum.ACTIVE,
            user_balance=[UserBalance(currency=str(currency.value), amount=0) for currency in CurrencyEnum],
        )
        created_user = await self.user_dao.create(user_orm)
        return ResponseUserModel.model_validate(created_user)

    async def change_status(self, user_uuid: UUID, new_status: UserStatusEnum) -> RequestUserModel:
        user = await self.user_dao.get_by_uuid(user_uuid)
        if not user:
            raise UserNotExistsException()

        status_str = str(new_status.value)
        if user.status == new_status.value:
            if new_status == UserStatusEnum.ACTIVE:
                raise UserAlreadyActiveException()
            raise UserAlreadyBlockedException()

        changed_user = await self.user_dao.update_status(user_uuid, status_str)
        return RequestUserModel.model_validate(changed_user)
