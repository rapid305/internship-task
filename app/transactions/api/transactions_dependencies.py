from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.outbox.outbox_service import OutboxService
from app.transactions.dao.transactions_dao import TransactionsDAO
from app.transactions.db.db_config import get_async_session
from app.transactions.service.transaction_service import TransactionService


def get_transaction_dao(
    session: AsyncSession = Depends(get_async_session),
) -> TransactionsDAO:
    return TransactionsDAO(session=session)


def get_transaction_service(
    session: AsyncSession = Depends(get_async_session),
) -> TransactionService:
    return TransactionService(session=session, outbox_service=OutboxService(session))
