import logging
from typing import Any, Dict

from app.outbox.event_handlers import EventHandler
from app.outbox.kafka_producer import kafka_producer

logger = logging.getLogger(__name__)


class UserEventHandler(EventHandler):
    """Handler for user-related events - публикует в Kafka для других сервисов"""

    def supports(self, event_type: str) -> bool:
        """Support user-related events."""
        return event_type in ["USER_CREATED", "USER_STATUS_CHANGED", "BALANCE_UPDATED"]

    async def handle(self, payload: Dict[str, Any]) -> None:
        """Handle user events and publish to Kafka"""
        event_type = payload.get("event_type")
        user_id = payload.get("user_id")
        email = payload.get("email")

        if event_type == "USER_CREATED":
            logger.info(f"User created: {email} (ID: {user_id})")

            await kafka_producer.send_event(
                "user.created",
                {
                    "event_type": "user.created",
                    "event_id": user_id,
                    "payload": {"user_id": user_id, "email": email, "status": payload.get("status", "ACTIVE")},
                },
            )
            logger.info(f"Published user.created event to Kafka: {user_id}")

        elif event_type == "USER_STATUS_CHANGED":
            old_status = payload.get("old_status")
            new_status = payload.get("new_status")
            logger.info(f"User status changed: {email} ({old_status} to {new_status})")

            if new_status == "BLOCKED":
                await kafka_producer.send_event(
                    "user.blocked",
                    {
                        "event_type": "user.blocked",
                        "event_id": user_id,
                        "payload": {
                            "user_id": user_id,
                            "email": email,
                            "old_status": old_status,
                            "new_status": new_status,
                        },
                    },
                )
                logger.info(f"Published user.blocked event to Kafka: {user_id}")

        elif event_type == "BALANCE_UPDATED":
            logger.info(f"Balance updated for user {user_id}")
