import logging
from typing import Any, Dict

from app.outbox.event_handlers import EventHandler

logger = logging.getLogger(__name__)


class UserEventHandler(EventHandler):
    """Handler for user-related events"""

    async def handle(self, payload: Dict[str, Any]) -> None:
        """Handle user events"""
        event_type = payload.get("event_type", "UNKNOWN")
        user_id = payload.get("user_id")
        email = payload.get("email")

        if event_type == "USER_CREATED":
            logger.info(f"User created: {email} (ID: {user_id})")
        elif event_type == "USER_STATUS_CHANGED":
            old_status = payload.get("old_status")
            new_status = payload.get("new_status")
            logger.info(f"User status changed: {email} ({old_status} to {new_status})")

    def supports(self, event_type: str) -> bool:
        """Supported event types"""
        return event_type in ["USER_CREATED", "USER_STATUS_CHANGED"]
