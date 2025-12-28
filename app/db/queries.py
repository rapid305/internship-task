from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.schemas import CurrencyEnum
from app.db.models import User
from app.schemas.transaction_schemas import TaskReturn
from app.settings import settings


class MetricsCalculator:
    def __init__(self, session: AsyncSession, dt_gt: date, dt_lt: date):
        self.session = session
        self.dt_gt = dt_gt
        self.dt_lt = dt_lt
        self.users: Sequence[User] = []
        self.offset = settings.analytics.pagination.offset
        self.limit = settings.analytics.pagination.limit

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

    async def fetch_users_and_transactions(self, offset: int, limit: int) -> Sequence[User]:
        q = (
            select(User)
            .options(selectinload(User.user_transactions))
            .where(
                and_(
                    func.date(User.created) >= self.dt_gt,
                    func.date(User.created) <= self.dt_lt,
                )
            )
            .order_by(User.uuid)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        self.users = result.scalars().all()
        return self.users

    async def calculate_metrics(self) -> TaskReturn:

        registered_users_count = 0
        registered_and_deposit_users_count = 0
        registered_and_not_rollbacked_deposit_users_count = 0
        not_rollbacked_deposit_amount = Decimal("0.0")
        not_rollbacked_withdraw_amount = Decimal("0.0")
        transactions_count = 0
        not_rollbacked_transactions_count = 0

        current_offset = self.offset

        while True:
            users = await self.fetch_users_and_transactions(current_offset, self.limit)

            if not users:
                break

            registered_users_count += len(users)

            for user in self.users:
                has_deposit = False
                has_not_rollbacked_deposit = False

                for transaction in user.user_transactions:
                    created_date = transaction.created.date()
                    if not (self.dt_gt <= created_date <= self.dt_lt):
                        continue

                    transactions_count += 1

                    is_not_rollbacked = transaction.status != "ROLLBACKED"
                    if is_not_rollbacked:
                        not_rollbacked_transactions_count += 1

                    amount_decimal = Decimal(str(transaction.amount))
                    rate = self.exchange_rates_to_usd.get(CurrencyEnum(transaction.currency), Decimal("0"))

                    if transaction.amount > 0:
                        has_deposit = True
                        if is_not_rollbacked:
                            has_not_rollbacked_deposit = True
                            not_rollbacked_deposit_amount += amount_decimal * rate
                    elif transaction.amount < 0:
                        if is_not_rollbacked:
                            not_rollbacked_withdraw_amount += amount_decimal * rate

                if has_deposit:
                    registered_and_deposit_users_count += 1
                if has_not_rollbacked_deposit:
                    registered_and_not_rollbacked_deposit_users_count += 1

            current_offset += self.limit

        return TaskReturn(
            registered_users_count=registered_users_count,
            registered_and_deposit_users_count=registered_and_deposit_users_count,
            registered_and_not_rollbacked_deposit_users_count=registered_and_not_rollbacked_deposit_users_count,
            not_rollbacked_deposit_amount=not_rollbacked_deposit_amount,
            not_rollbacked_withdraw_amount=not_rollbacked_withdraw_amount,
            transactions_count=transactions_count,
            not_rollbacked_transactions_count=not_rollbacked_transactions_count,
        )


async def get_metrics(session: AsyncSession, dt_gt: date, dt_lt: date) -> TaskReturn:
    calculator = MetricsCalculator(session=session, dt_gt=dt_gt, dt_lt=dt_lt)
    return await calculator.calculate_metrics()
