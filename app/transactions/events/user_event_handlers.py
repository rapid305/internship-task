import logging
from typing import Any, Dict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.transactions.db.db_config import session_maker
from app.transactions.db.models import UserProjection

logger = logging.getLogger(__name__)


async def _get_or_create_projection(session: AsyncSession, user_id: str) -> UserProjection:
    stmt = select(UserProjection).where(UserProjection.uuid == user_id)
    result = await session.execute(stmt)
    projection = result.scalar_one_or_none()
    if projection is None:
        projection = UserProjection(uuid=user_id, user_status="ACTIVE")
        session.add(projection)
        await session.flush()
    return projection


async def handle_user_created(payload: Dict[str, Any]) -> None:
    """Handler of user_created event."""
    user_id = payload.get("user_id")
    status = payload.get("status", "ACTIVE")

    if not user_id:
        logger.warning("user.created payload without user_id: %s", payload)
        return

    async with session_maker() as session:
        try:
            projection = await _get_or_create_projection(session, user_id)
            projection.user_status = status
            await session.commit()
            logger.info("UserProjection upserted for user %s with status %s", user_id, status)
        except Exception:
            logger.exception("Failed to handle user.created for user %s", user_id)
            await session.rollback()
            raise


async def handle_user_blocked(payload: Dict[str, Any]) -> None:
    """Handler of user_blocked event. Marks user as BLOCKED in UserProjection."""
    user_id = payload.get("user_id")

    if not user_id:
        logger.warning("user.blocked payload without user_id: %s", payload)
        return

    async with session_maker() as session:
        try:
            stmt = update(UserProjection).where(UserProjection.uuid == user_id).values(user_status="BLOCKED")
            result = await session.execute(stmt)
            if result.rowcount == 0:
                projection = UserProjection(uuid=user_id, user_status="BLOCKED")
                session.add(projection)
            await session.commit()
            logger.info("UserProjection set to BLOCKED for user %s", user_id)
        except Exception:
            logger.exception("Failed to handle user.blocked for user %s", user_id)
            await session.rollback()
            raise
