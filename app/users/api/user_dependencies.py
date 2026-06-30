from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.outbox.outbox_service import OutboxService
from app.users.dao.users_dao import UsersDAO
from app.users.db.db_config import get_async_session
from app.users.service.user_service import UserService


def get_users_dao(
    session: AsyncSession = Depends(get_async_session),
) -> UsersDAO:
    return UsersDAO(session)


def get_outbox_service(
    session: AsyncSession = Depends(get_async_session),
) -> OutboxService:
    return OutboxService(session)


def get_user_service(
    session: AsyncSession = Depends(get_async_session),
) -> UserService:
    return UserService(session=session, outbox_service=OutboxService(session))
