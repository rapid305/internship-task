import asyncio
from decimal import Decimal
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db_config import Base
from app.core.schemas import CurrencyEnum
from app.transactions.schemas import TransactionAnalyticsSchema
from app.users.api.user_dependencies import get_user_service
from app.users.dao.users_dao import UsersDAO
from app.users.db.models import User
from app.users.main import app
from app.users.schemas.user_schemas import CreateUserModel, ResponseUserBalanceModel, UserStatusEnum
from app.users.service.user_service import UserService
from app.users.settings import settings

settings.setenv("testing")

TEST_DB_URL = settings.get("DB.URL")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(
        TEST_DB_URL,
        echo=False,
        pool_pre_ping=True,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture(scope="session")
async def session_maker(engine):
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture(scope="function")
async def db_session(session_maker, engine) -> AsyncGenerator[AsyncSession | Any, Any]:
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
def test_uuid() -> UUID:
    """Fixture for generating test UUIDs."""
    return uuid4()


@pytest.fixture
def mock_user_factory():
    """Factory fixture for creating mock users."""

    def create_mock_user(
        email: str = "test@example.com",
        password: str = "c4828408-eae7-4eb6-8351-a1226612a6f0",
        status: UserStatusEnum = UserStatusEnum.ACTIVE,
        user_uuid=None,
        with_balances: bool = False,
        balance_amount_usd: Decimal = Decimal("0.00"),
        balance_amount_eur: Decimal = Decimal("0.00"),
    ) -> MagicMock:
        """
        Create a mock user with specified attributes.

        Args:
            email: User email
            password: User password
            status: User status
            user_uuid: UUID for user (generated if None)
            with_balances: Whether to add balance mocks
            balance_amount_usd: USD balance amount
            balance_amount_eur: EUR balance amount
        """
        user_uuid = user_uuid or uuid4()

        mock_user = MagicMock()
        mock_user.uuid = user_uuid
        mock_user.password = password
        mock_user.email = email
        mock_user.status = status
        mock_user.created = None
        mock_user.updated = None

        if with_balances:
            mock_usd_balance = MagicMock()
            mock_usd_balance.currency = CurrencyEnum.USD
            mock_usd_balance.amount = balance_amount_usd

            mock_eur_balance = MagicMock()
            mock_eur_balance.currency = CurrencyEnum.EUR
            mock_eur_balance.amount = balance_amount_eur

            mock_user.user_balance = [mock_usd_balance, mock_eur_balance]
        else:
            mock_user.user_balance = []

        return mock_user

    return create_mock_user


@pytest.fixture
def default_mock_user(mock_user_factory):
    """Default mock user for tests."""
    return mock_user_factory(
        email="test@example.com",
        password="c4828408-eae7-4eb6-8351-a1226612a6f0",
        status=UserStatusEnum.ACTIVE,
        with_balances=True,
        balance_amount_usd=Decimal("0.00"),
        balance_amount_eur=Decimal("0.00"),
    )


@pytest.fixture
def mock_user_with_balances(mock_user_factory):
    """Mock user with balances."""
    return mock_user_factory(
        with_balances=True, balance_amount_usd=Decimal("100.00"), balance_amount_eur=Decimal("50.00")
    )


@pytest.fixture
def blocked_mock_user(mock_user_factory):
    """Blocked mock user."""
    return mock_user_factory(status=UserStatusEnum.BLOCKED)


@pytest_asyncio.fixture
def mock_transaction_analytics():
    """Fixture for mock TransactionAnalyticsSchema"""

    def _create(**kwargs):
        defaults = {
            "registered_users_count": kwargs.get("registered_users_count", 10),
            "registered_and_deposit_users_count": kwargs.get("registered_and_deposit_users_count", 5),
            "registered_and_not_rollbacked_deposit_users_count": kwargs.get(
                "registered_and_not_rollbacked_deposit_users_count", 4
            ),
            "not_rollbacked_deposit_amount": kwargs.get("not_rollbacked_deposit_amount", Decimal("1000.0")),
            "not_rollbacked_withdraw_amount": kwargs.get("not_rollbacked_withdraw_amount", Decimal("500.0")),
            "transactions_count": kwargs.get("transactions_count", 20),
            "not_rollbacked_transactions_count": kwargs.get("not_rollbacked_transactions_count", 18),
        }
        return TransactionAnalyticsSchema(**defaults)

    return _create


@pytest.fixture
def mock_user_service():
    """Mock UserService for API tests."""
    service = AsyncMock(spec=UserService)
    return service


@pytest.fixture
def app_with_overrides(mock_user_service):
    """App with overridden dependencies."""
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app_with_overrides):
    """Async test client."""
    async with AsyncClient(app=app_with_overrides, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_user_data(test_uuid):
    """Sample user data for API responses."""
    return {
        "uuid": str(test_uuid),
        "email": "test@example.com",
        "password": "c4828408-eae7-4eb6-8351-a1226612a6f0",
        "status": "ACTIVE",
        "created": None,
        "updated": None,
        "user_balance": [],
    }


@pytest_asyncio.fixture
async def users_dao(db_session: AsyncSession):
    """Fixture for UsersDAO"""
    return UsersDAO(db_session)


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, users_dao: UsersDAO) -> User:
    user = CreateUserModel(
        email="test@example.com",
        password="c4828408-eae7-4eb6-8351-a1226612a6f0",
        status=UserStatusEnum.ACTIVE,
        user_balance=[
            ResponseUserBalanceModel(currency=CurrencyEnum.USD, amount=Decimal("0.00")),
            ResponseUserBalanceModel(currency=CurrencyEnum.EUR, amount=Decimal("0.00")),
        ],
    )

    user = await users_dao.create_user_with_balance(user)
    return user
