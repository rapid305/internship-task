from decimal import Decimal
from uuid import UUID

from app.core.schemas import CurrencyEnum
from app.db.dao.transactions_dao import TransactionsDAO
from app.db.dao.users_dao import UsersDAO
from app.exceptions.common_exceptions import BadRequestDataException
from app.exceptions.transaction_exceptions import (
    NegativeBalanceException,
    TransactionAlreadyRollbackedException,
    TransactionDoesNotBelongToUserException,
    TransactionNotExistsException,
)
from app.exceptions.user_exceptions import (
    CreateTransactionForBlockedUserException,
    UpdateTransactionForBlockedUserException,
)
from app.schemas.transaction_schemas import (
    CreateTransactionModel,
    RequestTransactionModel,
    TransactionModel,
    TransactionStatusEnum,
)


class TransactionService:
    def __init__(self, transaction_dao: TransactionsDAO, user_dao: UsersDAO):
        self.transaction_dao = transaction_dao
        self.user_dao = user_dao

    async def create_transaction(
        self,
        user_uuid: UUID,
        transaction_data: RequestTransactionModel,
    ) -> TransactionModel:
        """Creates a new transaction."""
        if transaction_data.amount == 0:
            raise BadRequestDataException()

        user = await self.user_dao.get_by_uuid(user_uuid, raise_not_found=True)

        if user.status != "ACTIVE":
            raise CreateTransactionForBlockedUserException()

        user_balance = await self.user_dao.get_by_user_and_currency(
            user_uuid,
            transaction_data.currency,
        )

        if user_balance is None:
            current_balance = Decimal("0.00")
        else:
            current_balance = user_balance.amount

        new_balance = current_balance + transaction_data.amount
        if new_balance < 0:
            raise NegativeBalanceException()

        await self.user_dao.update_balance(user_uuid, transaction_data.currency, new_balance, should_commit=True)

        create_model = CreateTransactionModel(
            user_uuid=user_uuid,
            currency=transaction_data.currency,
            amount=transaction_data.amount,
            status=TransactionStatusEnum.processed,
        )

        transaction = await self.transaction_dao.create(create_model)

        return TransactionModel(
            uuid=transaction.uuid,
            user_uuid=transaction.user_uuid,
            currency=CurrencyEnum(transaction.currency),
            amount=transaction.amount,
            status=TransactionStatusEnum(transaction.status),
            created=transaction.created,
            updated=transaction.updated,
        )

    async def get_user_transactions(self, user_uuid: UUID) -> list[TransactionModel]:
        """Receive all transactions for a user"""
        transactions = await self.transaction_dao.get(user_uuid)

        return [
            TransactionModel(
                uuid=t.uuid,
                user_uuid=t.user_uuid,
                currency=CurrencyEnum(t.currency),
                amount=t.amount,
                status=TransactionStatusEnum(t.status),
                created=t.created,
                updated=t.updated,
            )
            for t in transactions
        ]

    async def update_transaction(self, user_uuid: UUID, transaction_uuid: UUID) -> None:
        """Update transaction."""
        db_user = await self.user_dao.get_by_uuid(user_uuid, raise_not_found=True)
        db_transaction = await self.transaction_dao.get_by_uuid(transaction_uuid)

        if not db_transaction:
            raise TransactionNotExistsException()
        if db_transaction.user_uuid != db_user.uuid:
            raise TransactionDoesNotBelongToUserException()
        if db_transaction.status == "ROLLBACKED":
            raise TransactionAlreadyRollbackedException()
        if db_user.status == "BLOCKED":
            raise UpdateTransactionForBlockedUserException()

        db_user_balance = await self.user_dao.get_by_user_and_currency(user_uuid, db_transaction.currency)

        if db_user_balance is None:
            current_balance = Decimal("0.00")
        else:
            current_balance = db_user_balance.amount

        if db_transaction.amount < 0:
            new_amount = current_balance + abs(db_transaction.amount)
        else:
            new_amount = current_balance - db_transaction.amount

        if new_amount < 0:
            raise NegativeBalanceException()

        await self.user_dao.update_balance(user_uuid, db_transaction.currency, new_amount, should_commit=True)

        await self.transaction_dao.update_by_uuid(
            transaction_uuid, status=TransactionStatusEnum.roll_backed, should_commit=True
        )
