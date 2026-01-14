from decimal import Decimal

import pytest

from app.core.schemas import CurrencyEnum
from app.users.db.models import User
from app.users.schemas.user_schemas import CreateUserModel, ResponseUserBalanceModel, UserFilters, UserStatusEnum


class TestUsersDAO:
    """Tests for User Data Access Object (DAO) operations."""

    @pytest.mark.asyncio
    async def test_create_user_with_balance(self, users_dao):
        """Test creating a user with an initial balance."""
        user_data = CreateUserModel(
            email="create_test@example.com",
            status=UserStatusEnum.ACTIVE,
            user_balance=[
                ResponseUserBalanceModel(currency=CurrencyEnum.USD, amount=Decimal("100.00")),
                ResponseUserBalanceModel(currency=CurrencyEnum.EUR, amount=Decimal("50.00")),
            ],
        )

        created_user = await users_dao.create_user_with_balance(user_data)

        assert isinstance(created_user, User)
        assert created_user.email == "create_test@example.com"
        assert created_user.status == UserStatusEnum.ACTIVE
        assert created_user.user_balance is not None
        assert len(created_user.user_balance) == 2

    @pytest.mark.asyncio
    async def test_get_user(self, users_dao, test_user):
        """Test retrieving a user by UUID."""
        fetched_users = await users_dao.get(uuid=test_user.uuid)

        assert len(fetched_users) == 1
        fetched_user = fetched_users[0]
        assert fetched_user.uuid == test_user.uuid
        assert fetched_user.email == test_user.email
        assert fetched_user.status == test_user.status

    @pytest.mark.asyncio
    async def test_get_by_email(self, users_dao, test_user):
        """Test retrieving a user by email."""
        fetched_user = await users_dao.get_by_email(test_user.email)

        assert fetched_user is not None
        assert fetched_user.uuid == test_user.uuid
        assert fetched_user.email == test_user.email
        assert fetched_user.status == test_user.status

    @pytest.mark.asyncio
    async def test_update_status(self, users_dao, test_user):
        """Test updating a user's status."""
        new_status = UserStatusEnum.BLOCKED
        updated_user = await users_dao.update_status(test_user.uuid, new_status)

        assert updated_user is not None
        assert updated_user.uuid == test_user.uuid
        assert updated_user.status == new_status

    @pytest.mark.asyncio
    async def test_get_all_with_balances(self, users_dao, test_user):
        """Test retrieving all users with their balances."""
        users = await users_dao.get_all_with_balances()

        assert len(users) > 0
        for user in users:
            assert user.user_balance is not None

    @pytest.mark.asyncio
    async def test_get_all_with_balances_with_filters(self, users_dao, test_user):
        """Test retrieving users with balances using filters."""
        filters = UserFilters(status=UserStatusEnum.ACTIVE)
        users = await users_dao.get_all_with_balances(filters=filters)

        assert len(users) > 0
        for user in users:
            assert user.status == UserStatusEnum.ACTIVE
            assert user.user_balance is not None

    @pytest.mark.asyncio
    async def test_update_balance(self, users_dao, test_user):
        """Test updating a user's balance."""
        currency = test_user.user_balance[0].currency
        new_amount = Decimal("100.00")

        updated_balance = await users_dao.update_balance(
            user_uuid=test_user.uuid,
            currency=currency,
            new_amount=new_amount,
        )

        assert updated_balance is not None
        assert updated_balance.amount == new_amount

    @pytest.mark.asyncio
    async def test_get_by_uuid_non_existent_user(self, users_dao):
        """Test retrieving a user by UUID that does not exist."""
        fetched_user = await users_dao.get_by_uuid("00000000-0000-0000-0000-000000000000")

        assert fetched_user is None

    @pytest.mark.asyncio
    async def test_get_by_user_and_currency(self, users_dao, test_user):
        """Test retrieving a user's balance by currency."""
        currency = test_user.user_balance[0].currency

        fetched_balance = await users_dao.get_by_user_and_currency(
            user_uuid=test_user.uuid,
            currency=currency,
        )

        assert fetched_balance is not None
        assert fetched_balance.currency == currency
        assert fetched_balance.amount == 0.0
