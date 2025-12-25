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
    """Service for managing user transactions."""

    def __init__(self, transaction_dao: TransactionsDAO, user_dao: UsersDAO):
        self.transaction_dao = transaction_dao
        self.user_dao = user_dao

    async def create_transaction(
        self,
        user_uuid: UUID,
        transaction_data: RequestTransactionModel,
    ) -> TransactionModel:
        """Creates a new transaction for a user."""
        self._validate_transaction_amount(transaction_data.amount)

        await self._get_active_user(user_uuid)
        current_balance = await self._get_user_balance(user_uuid, transaction_data.currency)

        new_balance = self._calculate_new_balance(current_balance, transaction_data.amount)
        self._validate_balance_not_negative(new_balance)

        await self.user_dao.update_balance(user_uuid, transaction_data.currency, new_balance, should_commit=True)

        transaction = await self._create_transaction_record(user_uuid, transaction_data)

        return self._build_transaction_model(transaction)

    async def get_user_transactions(self, user_uuid: UUID) -> list[TransactionModel]:
        """Retrieve all transactions for a specific user."""
        transactions = await self.transaction_dao.get(user_uuid)
        return [self._build_transaction_model(t) for t in transactions]

    async def update_transaction(self, user_uuid: UUID, transaction_uuid: UUID) -> None:
        """Rollback a transaction for a user."""
        user = await self.user_dao.get_by_uuid(user_uuid, raise_not_found=True)
        transaction = await self._get_user_transaction(user_uuid, transaction_uuid)

        self._validate_user_can_update_transaction(user, transaction)

        current_balance = await self._get_user_balance(user_uuid, transaction.currency)
        new_balance = self._calculate_rollback_balance(current_balance, transaction.amount)

        self._validate_balance_not_negative(new_balance)

        await self._update_user_balance(user_uuid, transaction, new_balance)
        await self._mark_transaction_as_rollbacked(transaction_uuid)

    async def _get_active_user(self, user_uuid: UUID):
        """Retrieve and validate user is active."""
        user = await self.user_dao.get_by_uuid(user_uuid, raise_not_found=True)

        if user.status != "ACTIVE":
            raise CreateTransactionForBlockedUserException()

        return user

    async def _get_user_balance(self, user_uuid: UUID, currency: CurrencyEnum) -> Decimal:
        """Get user's current balance for a specific currency."""
        user_balance = await self.user_dao.get_by_user_and_currency(user_uuid, currency)
        return user_balance.amount if user_balance else Decimal("0.00")

    async def _update_user_balance(self, user_uuid: UUID, transaction, new_balance: Decimal) -> None:
        """Update user's balance after rollback."""
        await self.user_dao.update_balance(user_uuid, transaction.currency, new_balance, should_commit=True)

    async def _mark_transaction_as_rollbacked(self, transaction_uuid: UUID) -> None:
        """Mark transaction as rollbacked in database."""
        await self.transaction_dao.update_by_uuid(
            transaction_uuid, status=TransactionStatusEnum.roll_backed, should_commit=True
        )

    async def _get_user_transaction(self, user_uuid: UUID, transaction_uuid: UUID):
        """Retrieve and validate transaction belongs to user."""
        transaction = await self.transaction_dao.get_by_uuid(transaction_uuid)

        if not transaction:
            raise TransactionNotExistsException()

        if transaction.user_uuid != user_uuid:
            raise TransactionDoesNotBelongToUserException()

        return transaction

    async def _create_transaction_record(self, user_uuid: UUID, transaction_data: RequestTransactionModel):
        """Create transaction record in database."""
        create_model = CreateTransactionModel(
            user_uuid=user_uuid,
            currency=transaction_data.currency,
            amount=transaction_data.amount,
            status=TransactionStatusEnum.processed,
        )

        return await self.transaction_dao.create(create_model)

    @staticmethod
    def _validate_transaction_amount(amount: Decimal) -> None:
        """Validate that transaction amount is not zero."""
        if amount == 0:
            raise BadRequestDataException()

    @staticmethod
    def _calculate_new_balance(current_balance: Decimal, amount: Decimal) -> Decimal:
        """Calculate new balance after transaction."""
        return current_balance + amount

    @staticmethod
    def _calculate_rollback_balance(current_balance: Decimal, transaction_amount: Decimal) -> Decimal:
        """Calculate new balance after rollback."""
        if transaction_amount < 0:
            return current_balance + abs(transaction_amount)
        return current_balance - transaction_amount

    @staticmethod
    def _build_transaction_model(transaction) -> TransactionModel:
        """Convert database transaction to TransactionModel."""
        return TransactionModel(
            uuid=transaction.uuid,
            user_uuid=transaction.user_uuid,
            currency=CurrencyEnum(transaction.currency),
            amount=transaction.amount,
            status=TransactionStatusEnum(transaction.status),
            created=transaction.created,
            updated=transaction.updated,
        )

    @staticmethod
    def _validate_user_can_update_transaction(user, transaction) -> None:
        """Validate that user can update/rollback the transaction."""
        if transaction.status == "ROLLBACKED":
            raise TransactionAlreadyRollbackedException()

        if user.status == "BLOCKED":
            raise UpdateTransactionForBlockedUserException()

    @staticmethod
    def _validate_balance_not_negative(balance: Decimal) -> None:
        """Validate that balance is not negative."""
        if balance < 0:
            raise NegativeBalanceException()
