import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def handle_user_created(payload: Dict[str, Any]) -> None:
    """Handler of user_created event."""
    user_id = payload.get("user_id")
    status = payload.get("status", "ACTIVE")

    logger.info(f"user created with id: {user_id} and status {status}")


async def handle_user_blocked(payload: Dict[str, Any]) -> None:
    """Handler of user_blocked event."""
    user_id = payload.get("user_id")

    logger.info("user.blocked payload with user_id: %s", user_id)
