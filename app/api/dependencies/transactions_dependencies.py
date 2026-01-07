from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dao.transactions_dao import TransactionsDAO
from app.db.db_config import get_async_session
from app.outbox.outbox_service import OutboxService
from app.services.transaction_service import TransactionService


def get_transaction_dao(
    session: AsyncSession = Depends(get_async_session),
) -> TransactionsDAO:
    return TransactionsDAO(session=session)


def get_transaction_service(
    session: AsyncSession = Depends(get_async_session),
) -> TransactionService:
    return TransactionService(session=session, outbox_service=OutboxService(session))
