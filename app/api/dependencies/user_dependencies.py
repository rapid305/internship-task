from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_config import get_async_session
from app.repositories.users.user_repository import UserRepository
from app.repositories.users.users_dao import UsersDAO
from app.services.user_service import UserService


def get_users_dao(
    session: AsyncSession = Depends(get_async_session),
) -> UsersDAO:
    return UsersDAO(session)


def get_user_repository(
    dao: UsersDAO = Depends(get_users_dao),
) -> UserRepository:
    return UserRepository(dao)


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repo)
