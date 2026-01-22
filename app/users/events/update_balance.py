import logging
from decimal import Decimal

from app.users.dao.users_dao import UsersDAO
from app.users.db.db_config import session_maker

logger = logging.getLogger(__name__)


async def handle_balance_updated(payload: dict) -> None:
    """Handler for balance.updated event."""
    user_id = payload.get("user_id")
    currency = payload.get("currency")
    delta = payload.get("amount")

    if not all([user_id, currency, delta]):
        logger.warning(f"Incomplete balance.updated payload: {payload}")
        return

    async with session_maker() as session:
        try:
            dao = UsersDAO(session)
            current_balance = await dao.get_by_user_and_currency(user_id, currency)

            if current_balance:
                new_amount = (current_balance.amount or Decimal("0")) + Decimal(str(delta))
            else:
                new_amount = Decimal(str(delta))

            await dao.update_balance(user_id, currency, new_amount, should_commit=True)
            logger.info(f"Balance updated for user {user_id}: {currency} += {delta} (new: {new_amount})")
        except Exception as e:
            logger.exception(f"Failed to update balance for user {user_id}: {e}")
