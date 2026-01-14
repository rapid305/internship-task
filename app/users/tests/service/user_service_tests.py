from decimal import Decimal

import pytest

from app.core.schemas import CurrencyEnum
from app.users.schemas.user_schemas import RequestUserModel, ResponseUserModel, UserFilters, UserStatusEnum


class TestUserService:

    @pytest.mark.asyncio
    async def test_get_users_without_filters(self, user_service, mock_user_dao, default_mock_user):
        """Test getting all users without filters."""
        mock_user_dao.get_all_with_balances.return_value = [default_mock_user]
        result = await user_service.get_users()

        assert len(result) == 1
        assert result[0].email == "test@example.com"
        mock_user_dao.get_all_with_balances.assert_called_once_with(filters=None)

    @pytest.mark.asyncio
    async def test_get_users_with_filters(self, user_service, mock_user_dao, default_mock_user):
        """Test getting users with filters."""
        filters = UserFilters(status=UserStatusEnum.ACTIVE)
        mock_user_dao.get_all_with_balances.return_value = [default_mock_user]

        result = await user_service.get_users(filters=filters)

        assert len(result) == 1
        mock_user_dao.get_all_with_balances.assert_called_once_with(filters=filters)

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_user_dao, mock_user_factory):
        """Test creating a user successfully."""
        user_request = RequestUserModel(email="newuser@example.com", password="password123")
        normalized_email = "newuser@example.com"

        mock_user_dao.get_by_email.return_value = None

        # Используем фабрику для создания мока
        mock_created_user = mock_user_factory(
            email=normalized_email,
            with_balances=True,
            balance_amount_usd=Decimal("0.00"),
            balance_amount_eur=Decimal("0.00"),
        )
        mock_user_dao.create_user_with_balance.return_value = mock_created_user

        result = await user_service.create_user(user_request)

        assert isinstance(result, ResponseUserModel)
        assert result.email == normalized_email
        mock_user_dao.get_by_email.assert_called_once_with(normalized_email)

    @pytest.mark.asyncio
    async def test_change_status_to_active_success(self, user_service, mock_user_dao, mock_user_factory, test_uuid):
        """Test changing user status to ACTIVE successfully."""
        user_uuid = test_uuid
        new_status = UserStatusEnum.ACTIVE

        # Создаем заблокированного пользователя
        mock_user = mock_user_factory(user_uuid=user_uuid, status=UserStatusEnum.BLOCKED)

        # Создаем обновленного пользователя
        mock_updated_user = mock_user_factory(user_uuid=user_uuid, status=UserStatusEnum.ACTIVE)

        mock_user_dao.get_by_uuid.return_value = mock_user
        mock_user_dao.update_status.return_value = mock_updated_user

        result = await user_service.change_status(user_uuid, new_status)

        assert result.status == UserStatusEnum.ACTIVE
        mock_user_dao.update_status.assert_called_once_with(user_uuid, new_status)

    @pytest.mark.asyncio
    async def test_change_status_to_blocked_success(self, user_service, mock_user_dao, mock_user_factory, test_uuid):
        """Test changing user status to BLOCKED successfully."""
        user_uuid = test_uuid
        new_status = UserStatusEnum.BLOCKED

        mock_user = mock_user_factory(user_uuid=user_uuid)
        mock_updated_user = mock_user_factory(user_uuid=user_uuid, status=UserStatusEnum.BLOCKED)

        mock_user_dao.get_by_uuid.return_value = mock_user
        mock_user_dao.update_status.return_value = mock_updated_user

        result = await user_service.change_status(user_uuid, new_status)

        assert result.status == UserStatusEnum.BLOCKED
        mock_user_dao.update_status.assert_called_once_with(user_uuid, new_status)

    @pytest.mark.asyncio
    async def test_create_user_email_normalization_short(self, user_service, mock_user_dao, mock_user_factory):
        """Short test for email normalization."""
        input_email = "Test@Example.COM "
        expected_email = "test@example.com"

        mock_user_dao.get_by_email.return_value = None

        mock_user_factory(email=expected_email)

        result = await user_service.create_user(RequestUserModel(email=input_email, password="testpass123"))

        assert result.email == expected_email
        mock_user_dao.get_by_email.assert_called_once_with(expected_email)

    @pytest.mark.asyncio
    async def test_get_users_with_balance_conversion(self, user_service, mock_user_dao, mock_user_with_balances):
        """Test that user balances are properly converted in response."""
        mock_user_dao.get_all_with_balances.return_value = [mock_user_with_balances]
        result = await user_service.get_users()

        assert len(result) == 1
        assert len(result[0].user_balance) == 2
        balance_currencies = {balance.currency for balance in result[0].user_balance}
        assert CurrencyEnum.USD in balance_currencies
        assert CurrencyEnum.EUR in balance_currencies

    @pytest.mark.asyncio
    async def test_create_user_with_all_currencies(self, user_service, mock_user_dao, default_mock_user):
        """Test that user is created with balances for all currencies."""
        user_request = RequestUserModel(email="test@example.com", password="password123")

        mock_user_dao.get_by_email.return_value = None
        mock_user_dao.create_user_with_balance.return_value = default_mock_user

        await user_service.create_user(user_request)

        call_args = mock_user_dao.create_user_with_balance.call_args[0][0]
        assert len(call_args.user_balance) == len(CurrencyEnum)

        created_currencies = {balance.currency for balance in call_args.user_balance}
        for currency in CurrencyEnum:
            assert currency in created_currencies
