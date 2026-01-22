from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Import fixtures from core - needed for pytest discovery
from app.core.conftest import (  # noqa: F401
    db_session,
    default_mock_user,
    engine,
    event_loop,
    mock_transaction_analytics,
    mock_user_factory,
    session_maker,
    test_user,
    test_uuid,
)
from app.outbox.outbox_service import OutboxService
from app.transactions.dao.transactions_dao import TransactionsDAO
from app.transactions.service.transaction_service import TransactionService
from app.users.dao.users_dao import UsersDAO


@pytest_asyncio.fixture
async def users_dao(db_session: AsyncSession):  # noqa: F811
    return UsersDAO(db_session)


@pytest_asyncio.fixture
async def transactions_dao(db_session: AsyncSession):  # noqa: F811
    return TransactionsDAO(db_session)


@pytest.fixture
def mock_transactions_dao():
    """Mock TransactionsDAO for unit tests."""
    return AsyncMock(spec=TransactionsDAO)


@pytest_asyncio.fixture
async def transaction_service(db_session: AsyncSession):  # noqa: F811
    mock_outbox_service = AsyncMock(spec=OutboxService)
    return TransactionService(session=db_session, outbox_service=mock_outbox_service)
