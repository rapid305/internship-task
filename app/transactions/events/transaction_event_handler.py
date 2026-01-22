import logging
from typing import Any, Dict

from app.outbox.event_handlers import EventHandler

logger = logging.getLogger(__name__)


class TransactionEventHandler(EventHandler):
    """Handler for transaction-related events"""

    async def handle(self, payload: Dict[str, Any]) -> None:
        """Handle transaction events"""
        event_type = payload.get("event_type", "UNKNOWN")
        transaction_id = payload.get("transaction_id")
        user_id = payload.get("user_id")
        amount = payload.get("amount") or payload.get("original_amount")
        currency = payload.get("currency")

        if event_type == "TRANSACTION_CREATED":
            logger.info(f"Transaction created: {amount} {currency} (ID: {transaction_id}, User: {user_id})")
        elif event_type == "TRANSACTION_ROLLBACKED":
            logger.info(f"Transaction rollbacked: {amount} {currency} (ID: {transaction_id}, User: {user_id})")

    def supports(self, event_type: str) -> bool:
        """Support only transaction-related events"""
        return event_type in ["TRANSACTION_CREATED", "TRANSACTION_ROLLBACKED"]
