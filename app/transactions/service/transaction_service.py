import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestDataException
from app.core.schemas import CurrencyEnum
from app.outbox.outbox_service import OutboxService
from app.transactions.dao.transactions_dao import TransactionsDAO
from app.transactions.exceptions import (
    NegativeBalanceException,
    TransactionAlreadyRollbackedException,
    TransactionDoesNotBelongToUserException,
    TransactionNotExistsException,
)
from app.transactions.schemas import (
    CreateTransactionModel,
    RequestTransactionModel,
    TransactionModel,
    TransactionStatusEnum,
)
from app.users.dao.users_dao import UsersDAO
from app.users.exceptions import (
    CreateTransactionForBlockedUserException,
    UpdateTransactionForBlockedUserException,
)

logger = logging.getLogger(__name__)


class TransactionService:
    """Service for managing user transactions."""

    def __init__(self, session: AsyncSession, outbox_service: OutboxService):
        self.session = session
        self.transaction_dao = TransactionsDAO(session)
        self.user_dao = UsersDAO(session)
        self.outbox_service = outbox_service

    async def create_transaction(
        self,
        user_uuid: UUID,
        transaction_data: RequestTransactionModel,
    ) -> TransactionModel:
        """Creates a new transaction for a user."""
        self._validate_transaction_amount(transaction_data.amount)

        current_balance = await self.user_dao.get_by_user_and_currency(user_uuid, transaction_data.currency)
        current_amount = current_balance.amount if current_balance else Decimal("0.00")

        new_balance = current_amount + transaction_data.amount
        self._validate_balance_not_negative(new_balance)

        transaction = await self._create_transaction_record(user_uuid, transaction_data)

        await self.outbox_service.add_event(
            aggregate_id=str(transaction.uuid),
            event_type="TRANSACTION_CREATED",
            payload={
                "event_type": "TRANSACTION_CREATED",
                "transaction_id": str(transaction.uuid),
                "user_id": str(user_uuid),
                "currency": transaction_data.currency.value,
                "amount": str(transaction_data.amount),
                "previous_balance": str(current_amount),
                "new_balance": str(new_balance),
            },
        )

        await self.outbox_service.add_event(
            aggregate_id=str(user_uuid),
            event_type="BALANCE_UPDATED",
            payload={
                "event_type": "BALANCE_UPDATED",
                "user_id": str(user_uuid),
                "currency": transaction_data.currency.value,
                "amount": str(transaction_data.amount),
            },
        )

        await self.session.commit()

        return self._build_transaction_model(transaction)

    async def get_user_transactions(self, user_uuid: UUID) -> list[TransactionModel]:
        """Retrieve all transactions for a specific user."""
        transactions = await self.transaction_dao.get(user_uuid)
        return [self._build_transaction_model(t) for t in transactions]

    async def update_transaction(self, user_uuid: UUID, transaction_uuid: UUID) -> TransactionModel:
        """Rollback a transaction for a user."""
        transaction = await self._get_user_transaction(user_uuid, transaction_uuid)

        stmt = await self.user_dao.get_by_uuid(user_uuid)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise CreateTransactionForBlockedUserException()

        self._validate_user_can_update_transaction(user, transaction)

        currency_enum = (
            CurrencyEnum(transaction.currency) if isinstance(transaction.currency, str) else transaction.currency
        )

        current_balance = await self.user_dao.get_by_user_and_currency(user_uuid, currency_enum)
        current_amount = current_balance.amount if current_balance else Decimal("0.00")

        new_balance = self._calculate_rollback_balance(current_amount, transaction.amount)

        self._validate_balance_not_negative(new_balance)

        await self._mark_transaction_as_rollbacked(transaction_uuid)

        await self.outbox_service.add_event(
            aggregate_id=str(transaction_uuid),
            event_type="TRANSACTION_ROLLBACKED",
            payload={
                "event_type": "TRANSACTION_ROLLBACKED",
                "transaction_id": str(transaction_uuid),
                "user_id": str(user_uuid),
                "currency": transaction.currency,
                "original_amount": str(transaction.amount),
                "balance_before_rollback": str(current_amount),
                "balance_after_rollback": str(new_balance),
            },
        )

        await self.outbox_service.add_event(
            aggregate_id=str(user_uuid),
            event_type="BALANCE_UPDATED",
            payload={
                "event_type": "BALANCE_UPDATED",
                "user_id": str(user_uuid),
                "currency": currency_enum.value,
                "amount": str(-transaction.amount),
            },
        )

        await self.session.commit()

        return self._build_transaction_model(transaction)

    async def _mark_transaction_as_rollbacked(self, transaction_uuid: UUID) -> None:
        """Mark transaction as rollbacked in database."""
        await self.transaction_dao.update_by_uuid(transaction_uuid, status=TransactionStatusEnum.roll_backed)

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
            currency=(
                CurrencyEnum(transaction.currency) if isinstance(transaction.currency, str) else transaction.currency
            ),
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

        if user.user_status == "BLOCKED":
            raise UpdateTransactionForBlockedUserException()

    @staticmethod
    def _validate_balance_not_negative(balance: Decimal) -> None:
        """Validate that balance is not negative."""
        if balance < 0:
            raise NegativeBalanceException()
