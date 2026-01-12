import json
import logging
from typing import Callable, Dict, List

from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)


class KafkaConsumer:
    """
    Asynchronous Kafka consumer for processing events in Transaction Service.

    Args:
        bootstrap_servers: Kafka broker address (kafka:9092 for Docker)
        group_id: Consumer group ID
        topics: List of topics to listen to (e.g., ["user.created", "user.updated"])
    """

    def __init__(self, bootstrap_servers: str, group_id: str, topics: List[str] = None):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics or []
        self.consumer = None
        self._running = False
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register an event handler for a specific event type.

        Args:
            event_type: Type of event to handle (e.g., "user.created")
            handler: Asynchronous function to handle the event
        """
        self.handlers[event_type] = handler
        logger.info(f"Handler registered for event type: {event_type}")

    async def start(self) -> None:
        """Start listening to Kafka topics"""
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )

        await self.consumer.start()
        self._running = True
        logger.info(f"Kafka Consumer started. Topics: {self.topics}")

        try:
            async for message in self.consumer:
                await self._handle_message(message)
        except Exception as e:
            logger.error(f"Kafka Consumer error: {str(e)}")
            raise
        finally:
            await self.consumer.stop()

    async def stop(self) -> None:
        """Stop listening to Kafka topics"""
        self._running = False
        logger.info("Kafka Consumer stopped")

    async def _handle_message(self, message) -> None:
        """
        Handle a single Kafka message.

        Args:
            message: Message from Kafka consumer to process
        """
        topic = message.topic
        value = message.value

        try:
            event_type = value.get("event_type")
            event_id = value.get("event_id")
            payload = value.get("payload") if "payload" in value else value

            logger.info(f"Received event: {event_type} from '{topic}' (ID: {event_id})")

            if event_type in self.handlers:
                handler = self.handlers[event_type]
                try:
                    await handler(payload)
                    logger.info(f"Event {event_id} processed successfully")
                except Exception as handler_error:
                    logger.error(f"Handler failed for event {event_id}: {handler_error}", exc_info=True)
            else:
                logger.warning(f"No handler found for event type: {event_type}")

        except Exception as e:
            logger.error(f"Error processing message from '{topic}': {str(e)}", exc_info=True)


def init_kafka_consumer(
    bootstrap_servers: str = "kafka:9092", group_id: str = "transaction-service", topics: List[str] = None
) -> KafkaConsumer:
    """
    Create and initialize a KafkaConsumer instance.

    Args:
        bootstrap_servers: Kafka broker address
        group_id: Consumer group ID
        topics: List of topics to subscribe to

    Returns:
        KafkaConsumer: Initialized Kafka consumer instance
    """
    consumer = KafkaConsumer(
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        topics=topics or ["user.created", "user.updated", "user.blocked"],
    )
    return consumer
