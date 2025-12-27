from datetime import datetime, timedelta, timezone

from app.db.db_config import async_session_maker
from app.db.queries import get_metrics
from app.taskiq_broker import broker


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

    dt_lt = datetime.now(timezone.utc).date()
    dt_gt = dt_lt - timedelta(days=6)

    async with async_session_maker() as session:
        for week_num in range(52):
            metrics = await get_metrics(session, dt_gt, dt_lt)

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
