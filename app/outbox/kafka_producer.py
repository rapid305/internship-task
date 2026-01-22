import json
import logging
from typing import Any, Dict, Optional

from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Asynchronous Kafka producer for publishing events."""

    def __init__(self, bootstrap_servers: str):
        """
        Args:
            bootstrap_servers: Address Kafka broker (e.g., kafka:9092 for Docker)
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        """Start the connection to Kafka"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers, value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            await self.producer.start()
            logger.info(f"Kafka Producer started: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            self.producer = None
            raise

    async def stop(self) -> None:
        """Stop the connection to Kafka"""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("Kafka Producer stopped")
            except Exception as e:
                logger.error(f"Failed to stop Kafka producer: {e}")
            finally:
                self.producer = None
        else:
            logger.info("Kafka Producer stop skipped: not started")

    async def send_event(self, topic: str, event: Dict[str, Any]) -> None:
        """
        Send an event to a specified Kafka topic.

        Args:
            topic: Name of the Kafka topic
            event: Event data to send
        """
        if not self.producer:
            raise RuntimeError("Producer not started. Call start() first")

        try:
            await self.producer.send_and_wait(topic, value=event)
            logger.info(f"Event sent to topic '{topic}': {event}")
        except Exception as e:
            logger.error(f"Failed to send event to '{topic}': {str(e)}")
            raise


kafka_producer = KafkaProducer(bootstrap_servers="kafka:9092")
