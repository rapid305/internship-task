from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import CurrencyEnum
from app.db.models import Transaction, User

EXCHANGE_RATES_TO_USD = {
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


async def get_registered_users_count(session: AsyncSession, dt_gt: date, dt_lt: date):
    q = select(User).where(and_(func.date(User.created) >= dt_gt, func.date(User.created) <= dt_lt))
    registered_users = await session.execute(q)
    registered_users = registered_users.fetchall()
    return len(registered_users)


async def get_registered_and_deposit_users_count(session: AsyncSession, dt_gt: date, dt_lt: date):
    result = 0
    q = select(User).where(and_(func.date(User.created) >= dt_gt, func.date(User.created) <= dt_lt))
    registered_users = await session.execute(q)
    registered_users = registered_users.scalars()
    for user in registered_users:
        q = select(Transaction).where(
            and_(
                func.date(Transaction.created) >= dt_gt,
                func.date(Transaction.created) <= dt_lt,
                Transaction.user_uuid == user.uuid,
                Transaction.amount > 0,
            )
        )
        deposits = await session.execute(q)
        deposits = deposits.fetchall()
        if len(deposits) > 0:
            result += 1
    return result


async def get_registered_and_not_rollbacked_deposit_users_count(session: AsyncSession, dt_gt: date, dt_lt: date):
    result = 0
    q = select(User).where(and_(func.date(User.created) >= dt_gt, func.date(User.created) <= dt_lt))
    registered_users = await session.execute(q)
    registered_users = registered_users.scalars()
    for user in registered_users:
        q = select(Transaction).where(
            and_(
                func.date(Transaction.created) >= dt_gt,
                func.date(Transaction.created) <= dt_lt,
                Transaction.user_uuid == user.uuid,
                Transaction.amount > 0,
                Transaction.status != "ROLLBACKED",
            )
        )
        not_rollbacked_deposits = await session.execute(q)
        not_rollbacked_deposits = not_rollbacked_deposits.fetchall()
        if len(not_rollbacked_deposits) > 0:
            result += 1
    return result


async def get_not_rollbacked_deposit_amount(session: AsyncSession, dt_gt: date, dt_lt: date):
    q = select(Transaction).where(
        and_(
            func.date(Transaction.created) >= dt_gt,
            func.date(Transaction.created) <= dt_lt,
            Transaction.amount > 0,
            Transaction.status != "ROLLBACKED",
        )
    )
    not_rollbacked_deposits = await session.execute(q)
    not_rollbacked_deposits = not_rollbacked_deposits.scalars()

    total = Decimal("0.0")
    for transaction in not_rollbacked_deposits:
        amount_decimal = Decimal(str(transaction.amount))
        rate = EXCHANGE_RATES_TO_USD[transaction.currency]
        total += amount_decimal * rate

    return float(total)


async def get_not_rollbacked_withdraw_amount(session: AsyncSession, dt_gt: date, dt_lt: date):
    q = select(Transaction).where(
        and_(
            func.date(Transaction.created) >= dt_gt,
            func.date(Transaction.created) <= dt_lt,
            Transaction.amount < 0,
            Transaction.status != "ROLLBACKED",
        )
    )
    not_rollbacked_withdraws = await session.execute(q)
    not_rollbacked_withdraws = not_rollbacked_withdraws.scalars()

    total = Decimal("0.0")
    for transaction in not_rollbacked_withdraws:
        amount_decimal = Decimal(str(transaction.amount))
        rate = EXCHANGE_RATES_TO_USD[transaction.currency]
        total += amount_decimal * rate

    return float(total)


async def get_transactions_count(session: AsyncSession, dt_gt: date, dt_lt: date):
    q = select(Transaction).where(
        and_(func.date(Transaction.created) >= dt_gt, func.date(Transaction.created) <= dt_lt)
    )
    transactions = await session.execute(q)
    transactions = transactions.fetchall()
    return len(transactions)


async def get_not_rollbacked_transactions_count(session: AsyncSession, dt_gt: date, dt_lt: date):
    q = select(Transaction).where(
        and_(
            func.date(Transaction.created) >= dt_gt,
            func.date(Transaction.created) <= dt_lt,
            Transaction.status != "ROLLBACKED",
        )
    )
    transactions = await session.execute(q)
    transactions = transactions.fetchall()
    return len(transactions)
