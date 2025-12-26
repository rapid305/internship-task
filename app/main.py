import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api.v1 import router
from app.db.db_config import create_db_and_tables
from app.taskiq_broker import broker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()

    if not broker.is_worker_process:
        logger.info("Starting broker...")
        await broker.startup()
        logger.info("Broker started successfully")
    state = {
        "database_ready": True,
        "broker_ready": True,
    }
    yield state

    if not broker.is_worker_process:
        logger.info("Shutting down broker...")
        await broker.shutdown()
        logger.info("Broker shutdown complete")


app = FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7999, reload=True)
