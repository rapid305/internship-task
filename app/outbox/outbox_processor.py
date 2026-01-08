import asyncio
import json
import logging
from typing import Callable, List

from app.outbox.event_handlers import EventHandler
from app.outbox.outbox_model import OutboxEvent
from app.outbox.outbox_service import OutboxService

logger = logging.getLogger(__name__)


class OutboxProcessor:
    """Processor for handling outbox events"""

    def __init__(
        self,
        session_maker: Callable,
        handlers: List[EventHandler],
        batch_size: int = 50,
        poll_interval: int = 5,
    ):
        self.session_maker = session_maker
        self.handlers = handlers
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.is_running = False

    async def start(self) -> None:
        """Start processing outbox events"""
        self.is_running = True
        logger.info("Starting OutboxProcessor")

        try:
            while self.is_running:
                await self._process_batch()
                await asyncio.sleep(self.poll_interval)
        except asyncio.CancelledError:
            logger.info("OutboxProcessor cancelled")
        except Exception as e:
            logger.error(f"Error in OutboxProcessor: {e}", exc_info=True)

    async def stop(self) -> None:
        """Stop processing outbox events"""
        self.is_running = False
        logger.info("OutboxProcessor stopped")

    async def _process_batch(self) -> None:
        """Process a batch of outbox events"""
        try:
            async with self.session_maker() as session:
                outbox_service = OutboxService(session)
                events = await outbox_service.get_unprocessed_events(self.batch_size)

                if not events:
                    return

                logger.info(f"Processing {len(events)} outbox events")

                for event in events:
                    await self._process_single_event(event, outbox_service)

                await session.commit()
        except Exception as e:
            logger.error(f"Batch processing error: {e}", exc_info=True)

    async def _process_single_event(self, event: OutboxEvent, outbox_service: OutboxService) -> None:
        """Process a single outbox event"""
        try:
            payload = json.loads(event.payload)
            handler = self._find_handler(event.event_type)

            if not handler:
                logger.warning(f"No handler found for event type: {event.event_type}")
                await outbox_service.mark_as_processed(event.uuid)
                return

            await handler.handle(payload)
            await outbox_service.mark_as_processed(event.uuid)
            logger.info(f"Event {event.uuid} processed successfully: {event.event_type}")

        except Exception as e:
            logger.error(f"Error processing event {event.uuid}: {e}", exc_info=True)
            await outbox_service.increment_retry_count(event.uuid)

    def _find_handler(self, event_type: str) -> EventHandler | None:
        """Find the appropriate handler for the given event type"""
        for handler in self.handlers:
            if handler.supports(event_type):
                return handler
        return None
