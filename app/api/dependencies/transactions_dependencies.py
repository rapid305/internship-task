from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.user_dependencies import UsersDAO, get_users_dao
from app.db.dao.transactions_dao import TransactionsDAO
from app.db.db_config import get_async_session
from app.services.transaction_service import TransactionService


def get_transaction_dao(
    session: AsyncSession = Depends(get_async_session),
) -> TransactionsDAO:
    return TransactionsDAO(session=session)


def get_transaction_service(
    transaction_dao: TransactionsDAO = Depends(get_transaction_dao),
    user_dao: UsersDAO = Depends(get_users_dao),
) -> TransactionService:
    return TransactionService(transaction_dao, user_dao)
