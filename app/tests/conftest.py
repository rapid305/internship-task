import asyncio
from decimal import Decimal
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.schemas import CurrencyEnum
from app.db.dao.transactions_dao import TransactionsDAO
from app.db.dao.users_dao import UsersDAO
from app.db.db_config import Base
from app.db.models import User
from app.schemas.user_schemas import CreateUserModel, ResponseUserBalanceModel, UserStatusEnum
from app.services.transaction_service import TransactionService
from app.settings import settings

settings.setenv("testing")

TEST_DB_URL = settings.db.url


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


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, users_dao: UsersDAO) -> User:
    user = CreateUserModel(
        email="test@example.com",
        status=UserStatusEnum.ACTIVE,
        user_balance=[
            ResponseUserBalanceModel(currency=CurrencyEnum.USD, amount=Decimal("0.00")),
            ResponseUserBalanceModel(currency=CurrencyEnum.EUR, amount=Decimal("0.00")),
        ],
    )

    user = await users_dao.create_user_with_balance(user)
    return user


@pytest_asyncio.fixture
async def transactions_dao(db_session: AsyncSession):
    return TransactionsDAO(db_session)


@pytest_asyncio.fixture
async def users_dao(db_session: AsyncSession):
    return UsersDAO(db_session)


@pytest_asyncio.fixture
async def transaction_service(transactions_dao: TransactionsDAO, users_dao: UsersDAO):
    return TransactionService(transaction_dao=transactions_dao, user_dao=users_dao)
