from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import CurrencyEnum
from app.transactions.db.models import Transaction
from app.transactions.schemas import TransactionAnalyticsSchema
from app.transactions.settings import settings


class MetricsCalculator:
    def __init__(self, session: AsyncSession, dt_gt: date, dt_lt: date):
        self.session = session
        self.dt_gt = dt_gt
        self.dt_lt = dt_lt
        self.transactions: Sequence[Transaction] = []
        self.offset = settings.get("ANALYTICS.PAGINATION.OFFSET")
        self.limit = settings.get("ANALYTICS.PAGINATION.LIMIT")

        self.exchange_rates_to_usd: dict[CurrencyEnum, Decimal] = self.get_exchange_rates()

    @staticmethod
    def get_exchange_rates() -> dict[CurrencyEnum, Decimal]:
        return {
            CurrencyEnum.USD: Decimal("1.0"),
            CurrencyEnum.EUR: Decimal("0.9342"),
            CurrencyEnum.AUD: Decimal("0.5447"),
            CurrencyEnum.CAD: Decimal("0.6162"),
            CurrencyEnum.ARS: Decimal("0.0009"),
            CurrencyEnum.PLN: Decimal("0.2343"),
            CurrencyEnum.BTC: Decimal("100000.0"),
            CurrencyEnum.ETH: Decimal("3557.3476"),
            CurrencyEnum.DOGE: Decimal("0.3627"),
            CurrencyEnum.USDT: Decimal("0.9709"),
        }

    async def fetch_users_and_transactions(self, offset: int, limit: int) -> Sequence[Transaction]:
        """Fetch transactions for the specified date range."""
        q = (
            select(Transaction)
            .where(
                and_(
                    func.date(Transaction.created) >= self.dt_gt,
                    func.date(Transaction.created) <= self.dt_lt,
                )
            )
            .order_by(Transaction.user_uuid)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        self.transactions = result.scalars().all()
        return self.transactions

    async def calculate_metrics(self) -> TransactionAnalyticsSchema:
        """Calculate transaction metrics for the specified date range."""
        transactions_count = 0
        not_rollbacked_transactions_count = 0
        not_rollbacked_deposit_amount = Decimal("0.0")
        not_rollbacked_withdraw_amount = Decimal("0.0")
        unique_users: set = set()
        unique_users_with_deposits: set = set()
        unique_users_with_not_rollbacked_deposits: set = set()

        current_offset = self.offset

        while True:
            transactions = await self.fetch_users_and_transactions(current_offset, self.limit)

            if not transactions:
                break

            for transaction in transactions:
                created_date = transaction.created.date()
                if not (self.dt_gt <= created_date <= self.dt_lt):
                    continue

                transactions_count += 1
                unique_users.add(transaction.user_uuid)

                is_not_rollbacked = transaction.status != "ROLLBACKED"
                if is_not_rollbacked:
                    not_rollbacked_transactions_count += 1

                amount_decimal = Decimal(str(transaction.amount))
                rate = self.exchange_rates_to_usd.get(CurrencyEnum(transaction.currency), Decimal("0"))

                if transaction.amount > 0:
                    unique_users_with_deposits.add(transaction.user_uuid)
                    if is_not_rollbacked:
                        unique_users_with_not_rollbacked_deposits.add(transaction.user_uuid)
                        not_rollbacked_deposit_amount += amount_decimal * rate
                elif transaction.amount < 0:
                    if is_not_rollbacked:
                        not_rollbacked_withdraw_amount += amount_decimal * rate

            current_offset += self.limit

        return TransactionAnalyticsSchema(
            registered_users_count=len(unique_users),
            registered_and_deposit_users_count=len(unique_users_with_deposits),
            registered_and_not_rollbacked_deposit_users_count=len(unique_users_with_not_rollbacked_deposits),
            not_rollbacked_deposit_amount=not_rollbacked_deposit_amount,
            not_rollbacked_withdraw_amount=not_rollbacked_withdraw_amount,
            transactions_count=transactions_count,
            not_rollbacked_transactions_count=not_rollbacked_transactions_count,
        )


async def get_metrics(session: AsyncSession, dt_gt: date, dt_lt: date) -> TransactionAnalyticsSchema:
    """Get transaction metrics for the specified date range."""
    calculator = MetricsCalculator(session=session, dt_gt=dt_gt, dt_lt=dt_lt)
    return await calculator.calculate_metrics()
