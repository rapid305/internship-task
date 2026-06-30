import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.outbox.balance_event_handler import BalanceEventHandler
from app.outbox.kafka_consumer import KafkaConsumer
from app.outbox.kafka_producer import kafka_producer
from app.outbox.outbox_processor import OutboxProcessor
from app.transactions.api.v1 import router as transactions_router_v1
from app.transactions.db.db_config import db
from app.transactions.events.transaction_event_handler import TransactionEventHandler
from app.transactions.events.user_event_handlers import (
    handle_user_blocked,
    handle_user_created,
)
from app.transactions.taskiq_broker import broker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    if not broker.is_worker_process:
        logger.info("Starting taskiq broker...")
        await broker.startup()
        logger.info("Broker taskiq started successfully")

    handlers = [
        TransactionEventHandler(),
        BalanceEventHandler(),
    ]
    processor = OutboxProcessor(db.session_maker, handlers)
    outbox_processor_task = asyncio.create_task(processor.start())
    logger.info("Outbox transaction service processor started")

    kafka_consumer = KafkaConsumer.init_kafka_consumer(
        bootstrap_servers="kafka:9092",
        group_id="transaction-service",
        topics=["user.created", "user.blocked", "user.updated"],
    )

    kafka_consumer.register_handler("user.created", handle_user_created)
    kafka_consumer.register_handler("user.blocked", handle_user_blocked)

    await kafka_consumer.start()
    logger.info("Kafka Consumer started for User Service events")

    kafka_consumer_task = asyncio.create_task(kafka_consumer.listen())

    await kafka_producer.start()

    state = {
        "database_ready": True,
        "broker_ready": True,
        "outbox_processor_ready": True,
        "kafka_consumer_ready": True,
    }
    yield state

    if outbox_processor_task:
        await processor.stop()
        await outbox_processor_task

    if kafka_consumer_task:
        await kafka_consumer.stop()
        await kafka_consumer_task

    await kafka_producer.stop()

    if not broker.is_worker_process:
        logger.info("Shutting down transaction broker...")
        await broker.shutdown()
        logger.info("Broker shutdown for transactions complete")


app = FastAPI(lifespan=lifespan)
app.include_router(transactions_router_v1)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
