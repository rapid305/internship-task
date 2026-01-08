import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.outbox.outbox_model import OutboxEvent
from app.outbox.outbox_processor import OutboxProcessor
from app.outbox.outbox_service import OutboxService
from tests.outbox.handlers import FailingEventHandler, FakeEventHandler


class TestOutboxPattern:

    @pytest.mark.asyncio
    async def test_get_unprocessed_events(self, db_session: AsyncSession):
        """Test retrieval of unprocessed outbox events"""
        outbox_service = OutboxService(db_session)

        for i in range(5):
            event = await outbox_service.add_event(
                aggregate_id=f"agg_{i}", event_type="TEST_EVENT", payload={"index": i}
            )
            if i % 2 == 0:
                event.processed = True
                event.processed_at = datetime.now(timezone.utc)

        await db_session.commit()

        unprocessed_events = await outbox_service.get_unprocessed_events(limit=10)

        assert len(unprocessed_events) == 2

        indices = [json.loads(event.payload)["index"] for event in unprocessed_events]
        assert set(indices) == {1, 3}

    @pytest.mark.asyncio
    async def test_outbox_processor_handler_not_found(
        self,
        db_session: AsyncSession,
        session_maker,
    ):
        """Test processor behavior when no handler found"""
        outbox_service = OutboxService(db_session)

        event = await outbox_service.add_event(
            aggregate_id=str(uuid4()), event_type="UNKNOWN_EVENT", payload={"test": "data"}
        )

        await db_session.commit()

        handler = FakeEventHandler()

        processor = OutboxProcessor(
            session_maker=session_maker,
            handlers=[handler],
            batch_size=10,
            poll_interval=0,
        )

        await processor._process_batch()

        assert len(handler.handled_payloads) == 0

        await db_session.refresh(event)

        assert event.processed is True
        assert event.processed_at is not None

    @pytest.mark.asyncio
    async def test_outbox_processor_error_handling(
        self,
        db_session: AsyncSession,
        session_maker,
    ):
        """Test processor error handling"""
        outbox_service = OutboxService(db_session)

        event = await outbox_service.add_event(
            aggregate_id=str(uuid4()), event_type="FAILING_EVENT", payload={"test": "data"}
        )

        await db_session.commit()

        initial_retry_count = event.retry_count

        processor = OutboxProcessor(
            session_maker=session_maker,
            handlers=[FailingEventHandler()],
            batch_size=10,
            poll_interval=0,
        )

        await processor._process_batch()

        await db_session.refresh(event)

        assert event.retry_count == initial_retry_count + 1
        assert event.processed is False
        assert event.next_retry_at is not None

    @pytest.mark.asyncio
    async def test_outbox_events_with_retry_delay(
        self,
        db_session: AsyncSession,
    ):
        """Test that events with future retry time are not picked up"""
        outbox_service = OutboxService(db_session)

        _ = await outbox_service.add_event(aggregate_id="agg_1", event_type="TEST_EVENT", payload={"index": 1})

        event2 = await outbox_service.add_event(aggregate_id="agg_2", event_type="TEST_EVENT", payload={"index": 2})
        event2.next_retry_at = datetime.now(timezone.utc) + timedelta(hours=1)

        event3 = await outbox_service.add_event(aggregate_id="agg_3", event_type="TEST_EVENT", payload={"index": 3})
        event3.next_retry_at = datetime.now(timezone.utc) - timedelta(minutes=1)

        await db_session.commit()

        unprocessed_events = await outbox_service.get_unprocessed_events(limit=10)

        assert len(unprocessed_events) == 2

        indices = [json.loads(event.payload)["index"] for event in unprocessed_events]
        assert set(indices) == {1, 3}

    @pytest.mark.asyncio
    async def test_mark_as_processed_updates_database(
        self,
        db_session: AsyncSession,
    ):
        """Test that mark_as_processed actually updates the database"""
        outbox_service = OutboxService(db_session)

        event = await outbox_service.add_event(
            aggregate_id=str(uuid4()), event_type="TEST_EVENT", payload={"test": "data"}
        )

        await db_session.commit()

        success = await outbox_service.mark_as_processed(event.uuid)
        assert success is True

        await db_session.commit()

        result = await db_session.execute(select(OutboxEvent).where(OutboxEvent.uuid == event.uuid))
        updated_event = result.scalar_one()

        assert updated_event.processed is True
        assert updated_event.processed_at is not None
        assert updated_event.retry_count == 0

    @pytest.mark.asyncio
    async def test_increment_retry_count_updates_database(
        self,
        db_session: AsyncSession,
    ):
        """Test that increment_retry_count actually updates the database"""
        outbox_service = OutboxService(db_session)

        event = await outbox_service.add_event(
            aggregate_id=str(uuid4()), event_type="TEST_EVENT", payload={"test": "data"}
        )

        await db_session.commit()

        initial_retry_count = event.retry_count

        success = await outbox_service.increment_retry_count(event.uuid)
        assert success is True

        await db_session.commit()

        result = await db_session.execute(select(OutboxEvent).where(OutboxEvent.uuid == event.uuid))
        updated_event = result.scalar_one()

        assert updated_event.retry_count == initial_retry_count + 1
        assert updated_event.next_retry_at is not None

    @pytest.mark.asyncio
    async def test_outbox_processor_handles_max_retries(
        self,
        db_session: AsyncSession,
        session_maker,
    ):
        """Test that processor doesn't process events with max retries exceeded"""
        outbox_service = OutboxService(db_session)

        event = await outbox_service.add_event(
            aggregate_id=str(uuid4()), event_type="FAILING_EVENT", payload={"test": "data"}
        )
        event.retry_count = 3

        await db_session.commit()

        handler = FailingEventHandler()

        processor = OutboxProcessor(
            session_maker=session_maker,
            handlers=[handler],
            batch_size=10,
            poll_interval=0,
        )

        await processor._process_batch()

        await db_session.refresh(event)
        assert event.retry_count == 3
        assert event.processed is False

    @pytest.mark.asyncio
    async def test_json_serialization_deserialization(
        self,
        db_session: AsyncSession,
    ):
        """Test that JSON serialization/deserialization works correctly"""
        outbox_service = OutboxService(db_session)

        complex_payload = {
            "string": "test",
            "number": 123,
            "float": 123.45,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }

        event = await outbox_service.add_event(
            aggregate_id=str(uuid4()), event_type="COMPLEX_EVENT", payload=complex_payload
        )

        await db_session.commit()

        assert isinstance(event.payload, str)

        deserialized = json.loads(event.payload)
        assert deserialized == complex_payload

    @pytest.mark.asyncio
    async def test_outbox_processor_commit_after_batch(
        self,
        db_session: AsyncSession,
        session_maker,
    ):
        """Test that processor commits changes after batch processing"""
        outbox_service = OutboxService(db_session)

        event_count = 3
        for i in range(event_count):
            await outbox_service.add_event(
                aggregate_id=f"agg_{i}", event_type="TRANSACTION_CREATED", payload={"index": i}
            )

        await db_session.commit()

        handler = FakeEventHandler()

        processor = OutboxProcessor(
            session_maker=session_maker,
            handlers=[handler],
            batch_size=10,
            poll_interval=0,
        )

        async with session_maker() as check_session:
            await processor._process_batch()

            result = await check_session.execute(select(OutboxEvent).where(OutboxEvent.processed.is_(True)))
            processed_events = result.scalars().all()

            assert len(processed_events) == event_count
