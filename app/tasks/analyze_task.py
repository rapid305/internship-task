from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_config import async_session_maker
from app.db.queries import (
    get_not_rollbacked_deposit_amount,
    get_not_rollbacked_transactions_count,
    get_not_rollbacked_withdraw_amount,
    get_registered_and_deposit_users_count,
    get_registered_and_not_rollbacked_deposit_users_count,
    get_registered_users_count,
    get_transactions_count,
)
from app.taskiq_broker import broker


async def collect_metrics(
    session: AsyncSession,
    dt_gt: date,
    dt_lt: date,
) -> dict[str, int | float]:
    """Collects metrics from database."""
    return {
        "registered_users_count": await get_registered_users_count(session, dt_gt=dt_gt, dt_lt=dt_lt),
        "registered_and_deposit_users_count": await get_registered_and_deposit_users_count(
            session, dt_gt=dt_gt, dt_lt=dt_lt
        ),
        "registered_and_not_rollbacked_deposit_users_count": (
            await get_registered_and_not_rollbacked_deposit_users_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        ),
        "not_rollbacked_deposit_amount": await get_not_rollbacked_deposit_amount(session, dt_gt=dt_gt, dt_lt=dt_lt),
        "not_rollbacked_withdraw_amount": await get_not_rollbacked_withdraw_amount(session, dt_gt=dt_gt, dt_lt=dt_lt),
        "transactions_count": await get_transactions_count(session, dt_gt=dt_gt, dt_lt=dt_lt),
        "not_rollbacked_transactions_count": await get_not_rollbacked_transactions_count(
            session, dt_gt=dt_gt, dt_lt=dt_lt
        ),
    }


def has_non_zero_metrics(metrics: dict) -> bool:
    """Not check if not null metrics."""
    for value in metrics.values():
        if isinstance(value, (int, float)) and value > 0:
            return True
    return False


@broker.task
async def get_transaction_analysis() -> list[dict]:
    """Analyze transactions for the last 52 weeks."""
    results: list[dict] = []

    dt_lt = datetime.now(datetime.UTC).date()
    dt_gt = dt_lt - timedelta(days=6)

    async with async_session_maker() as session:
        for week_num in range(52):
            metrics = await collect_metrics(session, dt_gt, dt_lt)

            if has_non_zero_metrics(metrics):
                results.append(
                    {
                        "week_number": week_num + 1,
                        "start_date": dt_gt.isoformat(),
                        "end_date": dt_lt.isoformat(),
                        **metrics,
                    }
                )

            dt_lt -= timedelta(weeks=1)
            dt_gt -= timedelta(weeks=1)

    results.sort(key=lambda x: x["week_number"])

    return results
