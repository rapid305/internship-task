import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.outbox.balance_event_handler import BalanceEventHandler
from app.outbox.kafka_consumer import KafkaConsumer
from app.outbox.kafka_producer import kafka_producer
from app.outbox.outbox_processor import OutboxProcessor
from app.users.api.v1 import router as v1_router
from app.users.db.db_config import db
from app.users.events.update_balance import handle_balance_updated
from app.users.events.user_event_handler import UserEventHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    await kafka_producer.start()
    logger.info("Kafka Producer started")

    handlers = [UserEventHandler(), BalanceEventHandler()]
    processor = OutboxProcessor(db.session_maker, handlers)
    outbox_processor_task = asyncio.create_task(processor.start())
    logger.info("Outbox user service processor started")

    kafka_consumer = KafkaConsumer.init_kafka_consumer(
        bootstrap_servers="kafka:9092", group_id="user-service", topics=["balance.updated"]
    )
    kafka_consumer.register_handler("BALANCE_UPDATED", handle_balance_updated)

    await kafka_consumer.start()
    kafka_consumer_task = asyncio.create_task(kafka_consumer.listen())
    logger.info("Kafka Consumer started for Transaction Service events")

    state = {
        "database_ready": True,
        "outbox_processor_ready": True,
        "kafka_producer_ready": True,
    }
    yield state

    if outbox_processor_task:
        await processor.stop()

    if kafka_consumer_task:
        await kafka_consumer.stop()
        await kafka_consumer_task

    await kafka_producer.stop()
    logger.info("Kafka Producer stopped")


app = FastAPI(lifespan=lifespan)
app.include_router(v1_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
