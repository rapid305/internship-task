import uuid
from decimal import Decimal

import pytest

from app.schemas.transaction_schemas import CreateTransactionModel, CurrencyEnum, TransactionStatusEnum


class TestTransactionsDAO:
    """Tests for TransactionsDAO"""

    @pytest.mark.asyncio
    async def test_create_transaction_works(self, test_user, transactions_dao, db_session):
        """Check if create() creates a transaction correctly"""

        create_data = CreateTransactionModel(
            user_uuid=test_user.uuid,
            amount=Decimal("100.50"),
            currency=CurrencyEnum.USDT,
            status=TransactionStatusEnum.processed,
        )

        transaction = await transactions_dao.create(create_data)

        assert transaction is not None
        assert transaction.uuid is not None
        assert transaction.user_uuid == test_user.uuid
        assert transaction.amount == Decimal("100.50")
        assert transaction.currency == "USDT"

    @pytest.mark.asyncio
    async def test_get_transactions_works(self, test_user, transactions_dao, db_session):
        """Check, if get() returns transactions for a user"""
        for i in range(3):
            await transactions_dao.create(
                CreateTransactionModel(
                    user_uuid=test_user.uuid,
                    amount=Decimal(f"{100 + i}.00"),
                    currency=CurrencyEnum.USDT,
                    status=TransactionStatusEnum.processed,
                ),
                should_commit=False,
            )

        await db_session.flush()

        transactions = await transactions_dao.get(test_user.uuid)

        assert len(transactions) == 3
        assert all(tx.user_uuid == test_user.uuid for tx in transactions)

    @pytest.mark.asyncio
    async def test_update_transaction_works(self, test_user, transactions_dao, db_session):
        """Check, if update_by_uuid() updates the transaction correctly"""
        create_data = CreateTransactionModel(
            user_uuid=test_user.uuid,
            amount=Decimal("50.00"),
            currency=CurrencyEnum.USDT,
            status=TransactionStatusEnum.processed,
        )
        transaction = await transactions_dao.create(create_data)

        updated = await transactions_dao.update_by_uuid(
            transaction.uuid,
            status="rollbacked",
            amount=Decimal("75.00"),
        )

        assert updated.uuid == transaction.uuid
        assert updated.status == "rollbacked"
        assert updated.amount == Decimal("75.00")

    @pytest.mark.asyncio
    async def test_get_by_uuid_works(self, test_user, transactions_dao, db_session):
        """Check, if get_by_uuid() finds the transaction by UUID"""
        create_data = CreateTransactionModel(
            user_uuid=test_user.uuid,
            amount=Decimal("25.00"),
            currency=CurrencyEnum.EUR,
            status=TransactionStatusEnum.processed,
        )
        transaction = await transactions_dao.create(create_data)

        found = await transactions_dao.get_by_uuid(transaction.uuid)

        assert found is not None
        assert found.uuid == transaction.uuid
        assert found.amount == Decimal("25.00")
        assert found.currency == "EUR"

    @pytest.mark.asyncio
    async def test_get_by_uuid_not_found(self, transactions_dao):
        """check, if get_by_uuid() returns None for non-existing UUID"""
        fake_uuid = uuid.uuid4()

        result = await transactions_dao.get_by_uuid(fake_uuid)

        assert result is None
