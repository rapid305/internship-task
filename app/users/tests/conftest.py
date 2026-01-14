from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient

# Import fixtures from core - needed for pytest discovery
from app.core.conftest import (  # noqa: F401
    app_with_overrides,
    db_session,
    default_mock_user,
    engine,
    event_loop,
    mock_user_factory,
    mock_user_service,
    session_maker,
    test_user,
    test_uuid,
)
from app.core.schemas import CurrencyEnum
from app.outbox.outbox_service import OutboxService
from app.users.dao.users_dao import UsersDAO
from app.users.db.models import User
from app.users.schemas.user_schemas import (
    CreateUserModel,
    ResponseUserBalanceModel,
    UserStatusEnum,
)
from app.users.service.user_service import UserService


@pytest_asyncio.fixture
async def users_dao(db_session):  # noqa: F811
    return UsersDAO(db_session)


@pytest.fixture
def mock_user_dao():
    """Mock UsersDAO for unit tests."""
    return AsyncMock(spec=UsersDAO)


@pytest_asyncio.fixture
async def user_service(db_session, mock_user_dao):  # noqa: F811
    mock_outbox_service = AsyncMock(spec=OutboxService)
    service = UserService(session=db_session, outbox_service=mock_outbox_service)
    service.user_dao = mock_user_dao
    return service


@pytest_asyncio.fixture
async def batch_users(db_session, users_dao: UsersDAO) -> list[User]:  # noqa: F811
    """Create multiple test users at once"""
    users_data = [
        {
            "email": "user1@example.com",
            "password": "c4828408-eae7-4eb6-8351-a1226612a6f0",
            "status": UserStatusEnum.ACTIVE,
            "balances": [
                ResponseUserBalanceModel(currency=CurrencyEnum.USD, amount=Decimal("100.00")),
            ],
        },
        {
            "email": "user2@example.com",
            "password": "c4828408-eae7-4eb6-8351-a1226612a6f0",
            "status": UserStatusEnum.ACTIVE,
            "balances": [
                ResponseUserBalanceModel(currency=CurrencyEnum.EUR, amount=Decimal("200.00")),
            ],
        },
        {
            "email": "user3@example.com",
            "password": "c4828408-eae7-4eb6-8351-a1226612a6f0",
            "status": UserStatusEnum.INACTIVE,
            "balances": [
                ResponseUserBalanceModel(currency=CurrencyEnum.USD, amount=Decimal("50.00")),
                ResponseUserBalanceModel(currency=CurrencyEnum.EUR, amount=Decimal("25.00")),
            ],
        },
    ]

    users = []
    for user_data in users_data:
        user = CreateUserModel(
            email=user_data["email"],
            password=user_data["password"],
            status=user_data["status"],
            user_balance=user_data["balances"],
        )
        created_user = await users_dao.create_user_with_balance(user)
        users.append(created_user)

    return users


@pytest.fixture
def mock_user_with_balances(mock_user_factory):  # noqa: F811
    """Mock user with balances."""
    return mock_user_factory(
        with_balances=True, balance_amount_usd=Decimal("100.00"), balance_amount_eur=Decimal("50.00")
    )


@pytest.fixture
def blocked_mock_user(mock_user_factory):  # noqa: F811
    """Blocked mock user."""
    return mock_user_factory(status=UserStatusEnum.BLOCKED)


@pytest.fixture
def sample_user_data(test_uuid):  # noqa: F811
    """Sample user data for API responses."""
    return {
        "uuid": str(test_uuid),
        "email": "test@example.com",
        "password": "password",
        "status": "ACTIVE",
        "created": None,
        "updated": None,
        "user_balance": [],
    }


@pytest_asyncio.fixture
async def client(app_with_overrides):  # noqa: F811
    """Async test client."""
    async with AsyncClient(app=app_with_overrides, base_url="http://test") as client:
        yield client
