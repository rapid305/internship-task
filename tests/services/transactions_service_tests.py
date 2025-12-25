from decimal import Decimal

import pytest

from app.exceptions.common_exceptions import BadRequestDataException
from app.exceptions.transaction_exceptions import NegativeBalanceException, TransactionAlreadyRollbackedException
from app.schemas.transaction_schemas import RequestTransactionModel, TransactionStatusEnum
from app.schemas.user_schemas import CurrencyEnum


class TestTransactionServiceCreateTransaction:
    """Tests for method create_transaction"""

    @pytest.mark.asyncio
    async def test_create_deposit_transaction(self, transaction_service, test_user):
        """Create a deposit transaction"""
        transaction_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("100.0"))

        result = await transaction_service.create_transaction(
            user_uuid=test_user.uuid, transaction_data=transaction_data
        )

        assert result.user_uuid == test_user.uuid
        assert result.currency == CurrencyEnum.USD
        assert result.amount == Decimal("100.0")
        assert result.status == TransactionStatusEnum.processed
        assert result.uuid is not None
        assert result.created is not None
        assert result.updated is not None

    @pytest.mark.asyncio
    async def test_create_withdrawal_transaction(self, transaction_service, test_user):
        """Create a withdrawal transaction"""
        deposit_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("200.0"))
        deposit_result = await transaction_service.create_transaction(
            user_uuid=test_user.uuid, transaction_data=deposit_data
        )
        assert deposit_result.amount == Decimal("200.0")

        withdrawal_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("-50.0"))

        result = await transaction_service.create_transaction(
            user_uuid=test_user.uuid, transaction_data=withdrawal_data
        )

        assert result.amount == Decimal("-50.0")
        assert result.status == TransactionStatusEnum.processed

    @pytest.mark.asyncio
    async def test_create_transaction_zero_amount(self, transaction_service, test_user):
        """Attempt to create a transaction with zero amount"""
        transaction_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("0.0"))

        with pytest.raises(BadRequestDataException):
            await transaction_service.create_transaction(user_uuid=test_user.uuid, transaction_data=transaction_data)

    @pytest.mark.asyncio
    async def test_create_transaction_negative_balance(self, transaction_service, test_user):
        """Attempt to create a withdrawal that would lead to a negative balance"""
        deposit_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("100.0"))
        await transaction_service.create_transaction(user_uuid=test_user.uuid, transaction_data=deposit_data)

        withdrawal_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("-150.0"))

        with pytest.raises(NegativeBalanceException):
            await transaction_service.create_transaction(user_uuid=test_user.uuid, transaction_data=withdrawal_data)

    @pytest.mark.asyncio
    async def test_create_transaction_different_currencies(self, transaction_service, test_user):
        """Create transactions in different currencies"""
        usd_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("100.0"))
        usd_result = await transaction_service.create_transaction(user_uuid=test_user.uuid, transaction_data=usd_data)
        assert usd_result.currency == CurrencyEnum.USD

        eur_data = RequestTransactionModel(currency=CurrencyEnum.EUR, amount=Decimal("50.0"))
        eur_result = await transaction_service.create_transaction(user_uuid=test_user.uuid, transaction_data=eur_data)
        assert eur_result.currency == CurrencyEnum.EUR


class TestTransactionServiceGetUserTransactions:
    """Tests for method get_user_transactions"""

    @pytest.mark.asyncio
    async def test_get_transactions_empty(self, transaction_service, test_user):
        """Receiving no transactions for a user"""
        result = await transaction_service.get_user_transactions(test_user.uuid)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_transactions_multiple(self, transaction_service, test_user):
        """Receiving multiple transactions for a user"""
        transactions_data = [
            RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("100.0")),
            RequestTransactionModel(currency=CurrencyEnum.EUR, amount=Decimal("50.0")),
            RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("200.0")),
        ]

        created_transactions = []
        for data in transactions_data:
            transaction = await transaction_service.create_transaction(user_uuid=test_user.uuid, transaction_data=data)
            created_transactions.append(transaction)

        result = await transaction_service.get_user_transactions(test_user.uuid)

        assert len(result) == 3

        for transaction in result:
            assert transaction.user_uuid == test_user.uuid

        amounts = [t.amount for t in result]
        assert Decimal("100.0") in amounts
        assert Decimal("50.0") in amounts
        assert Decimal("200.0") in amounts

        currencies = [t.currency for t in result]
        assert CurrencyEnum.USD in currencies
        assert CurrencyEnum.EUR in currencies


class TestTransactionServiceUpdateTransaction:
    """Tests for method update_transaction (rollback)"""

    @pytest.mark.asyncio
    async def test_rollback_deposit_transaction(self, transaction_service, test_user):
        """Rollback transaction on deposit (deduct money from the account)"""
        deposit_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("100.0"))
        transaction = await transaction_service.create_transaction(
            user_uuid=test_user.uuid, transaction_data=deposit_data
        )

        await transaction_service.update_transaction(user_uuid=test_user.uuid, transaction_uuid=transaction.uuid)

        transactions = await transaction_service.get_user_transactions(test_user.uuid)
        rollbacked_transaction = next(t for t in transactions if t.uuid == transaction.uuid)
        assert rollbacked_transaction.status == TransactionStatusEnum.roll_backed

    @pytest.mark.asyncio
    async def test_rollback_withdrawal_transaction(self, transaction_service, test_user):
        """Rollback transaction on withdrawal (refund money to the account)"""
        deposit_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("200.0"))
        await transaction_service.create_transaction(user_uuid=test_user.uuid, transaction_data=deposit_data)

        withdrawal_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("-50.0"))
        transaction = await transaction_service.create_transaction(
            user_uuid=test_user.uuid, transaction_data=withdrawal_data
        )

        await transaction_service.update_transaction(user_uuid=test_user.uuid, transaction_uuid=transaction.uuid)

        transactions = await transaction_service.get_user_transactions(test_user.uuid)
        rollbacked_transaction = next(t for t in transactions if t.uuid == transaction.uuid)
        assert rollbacked_transaction.status == TransactionStatusEnum.roll_backed

    @pytest.mark.asyncio
    async def test_rollback_withdrawal_when_balance_is_zero(self, transaction_service, test_user):
        """Rollback withdrawal when balance is zero (should raise NegativeBalanceException)"""
        withdrawal_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("-50.0"))

        with pytest.raises(NegativeBalanceException):
            await transaction_service.create_transaction(user_uuid=test_user.uuid, transaction_data=withdrawal_data)

        deposit_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("50.0"))
        await transaction_service.create_transaction(user_uuid=test_user.uuid, transaction_data=deposit_data)

        withdrawal_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("-50.0"))
        withdrawal_transaction = await transaction_service.create_transaction(
            user_uuid=test_user.uuid, transaction_data=withdrawal_data
        )

        await transaction_service.update_transaction(
            user_uuid=test_user.uuid, transaction_uuid=withdrawal_transaction.uuid
        )

    @pytest.mark.asyncio
    async def test_rollback_deposit_causes_negative_balance(self, transaction_service, test_user):
        """Rollback deposit that would cause negative balance (should raise NegativeBalanceException)"""
        deposit_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("100.0"))
        transaction = await transaction_service.create_transaction(
            user_uuid=test_user.uuid, transaction_data=deposit_data
        )

        withdrawal_data = RequestTransactionModel(currency=CurrencyEnum.USD, amount=Decimal("-80.0"))
        await transaction_service.create_transaction(user_uuid=test_user.uuid, transaction_data=withdrawal_data)

        with pytest.raises(NegativeBalanceException):
            await transaction_service.update_transaction(user_uuid=test_user.uuid, transaction_uuid=transaction.uuid)


@pytest.mark.asyncio
async def test_transaction_flow_complete_scenario(transaction_service, test_user):
    """Full scenario test: create, get, rollback, and error on double rollback"""
    transactions_to_create = [
        ("USD", Decimal("200.0")),
        ("USD", Decimal("-30.0")),
        ("EUR", Decimal("50.0")),
        ("USD", Decimal("-20.0")),
    ]

    created_transactions = []
    for currency_str, amount in transactions_to_create:
        currency = CurrencyEnum(currency_str)
        transaction_data = RequestTransactionModel(currency=currency, amount=amount)

        transaction = await transaction_service.create_transaction(
            user_uuid=test_user.uuid, transaction_data=transaction_data
        )
        created_transactions.append(transaction)

    all_transactions = await transaction_service.get_user_transactions(test_user.uuid)
    assert len(all_transactions) == 4

    transaction_to_rollback = created_transactions[1]
    await transaction_service.update_transaction(
        user_uuid=test_user.uuid, transaction_uuid=transaction_to_rollback.uuid
    )

    updated_transactions = await transaction_service.get_user_transactions(test_user.uuid)
    rollbacked_transaction = next(t for t in updated_transactions if t.uuid == transaction_to_rollback.uuid)
    assert rollbacked_transaction.status == TransactionStatusEnum.roll_backed

    with pytest.raises(TransactionAlreadyRollbackedException):
        await transaction_service.update_transaction(
            user_uuid=test_user.uuid, transaction_uuid=transaction_to_rollback.uuid
        )
