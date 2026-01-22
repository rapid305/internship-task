import logging
from typing import Any, Dict

from app.outbox.event_handlers import EventHandler
from app.outbox.kafka_producer import kafka_producer

logger = logging.getLogger(__name__)


class BalanceEventHandler(EventHandler):
    """Handle balance-related outbox events and publish them to Kafka."""

    def supports(self, event_type: str) -> bool:
        """Support balance update."""
        return event_type == "BALANCE_UPDATED"

    async def handle(self, payload: Dict[str, Any]) -> None:
        """Public event to Kafka topic 'balance.updated'."""
        try:
            await kafka_producer.send_event(topic="balance.updated", event=payload)
            logger.info(f"Balance event published to Kafka: {payload}")
        except Exception as e:
            logger.exception(f"Failed to publish balance event to Kafka: {e}")
            raise
