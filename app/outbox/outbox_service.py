import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Sequence
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.outbox.outbox_model import OutboxEvent

logger = logging.getLogger(__name__)


class OutboxService:
    """Service for managing outbox_tests events in the database."""

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 60

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_event(
        self,
        aggregate_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> OutboxEvent:
        """Add a new event to the outbox_tests"""
        try:
            event = OutboxEvent(
                aggregate_id=aggregate_id,
                event_type=event_type,
                payload=json.dumps(payload, default=str),
            )
            self.session.add(event)
            logger.debug(f"Added outbox_tests event: {event_type} for {aggregate_id}")
            return event
        except Exception as e:
            logger.error(f"Failed to add outbox_tests event: {e}")
            raise

    async def get_unprocessed_events(self, limit: int = 50) -> Sequence[OutboxEvent] | list[Any]:
        """Retrieve unprocessed events with retry logic"""
        try:
            query = (
                select(OutboxEvent)
                .where(OutboxEvent.processed.is_(False))
                .where(OutboxEvent.retry_count < self.MAX_RETRIES)
                .where(
                    (OutboxEvent.next_retry_at.is_(None)) | (OutboxEvent.next_retry_at <= datetime.now(timezone.utc))
                )
                .order_by(OutboxEvent.created_at.asc())
                .limit(limit)
            )
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get unprocessed events: {e}")
            return []

    async def mark_as_processed(self, event_uuid: UUID) -> bool:
        """Mark event as processed"""
        try:
            stmt = (
                update(OutboxEvent)
                .where(OutboxEvent.uuid == event_uuid)
                .values(processed=True, processed_at=datetime.now(timezone.utc), retry_count=0)
            )
            result = await self.session.execute(stmt)
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to mark event {event_uuid} as processed: {e}")
            return False

    async def increment_retry_count(self, event_uuid: UUID) -> bool:
        """Increment retry count and set next retry time"""
        try:
            next_retry = datetime.now(timezone.utc) + timedelta(seconds=self.RETRY_DELAY_SECONDS)
            stmt = (
                update(OutboxEvent)
                .where(OutboxEvent.uuid == event_uuid)
                .values(retry_count=OutboxEvent.retry_count + 1, next_retry_at=next_retry)
            )
            result = await self.session.execute(stmt)
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to increment retry count for {event_uuid}: {e}")
            return False

    async def delete_processed_events(self, days: int = 7) -> int:
        """Delete processed events older than specified days"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            query = (
                delete(OutboxEvent).where(OutboxEvent.processed.is_(True)).where(OutboxEvent.processed_at < cutoff_date)
            )

            result = await self.session.execute(query)
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} processed outbox_tests events")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete processed events: {e}")
            return 0

    async def get_failed_events(self, limit: int = 50) -> Sequence[OutboxEvent] | list[Any]:
        """Retrieve events that have exceeded max retries"""
        try:
            query = (
                select(OutboxEvent)
                .where(OutboxEvent.retry_count >= self.MAX_RETRIES)
                .where(OutboxEvent.processed.is_(False))
                .order_by(OutboxEvent.created_at.asc())
                .limit(limit)
            )
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get failed events: {e}")
            return []
