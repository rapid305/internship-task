from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dao.users_dao import UsersDAO
from app.db.db_config import get_async_session
from app.services.user_service import UserService


def get_users_dao(
    session: AsyncSession = Depends(get_async_session),
) -> UsersDAO:
    return UsersDAO(session)


def get_user_service(
    dao: UsersDAO = Depends(get_users_dao),
) -> UserService:
    return UserService(dao)
