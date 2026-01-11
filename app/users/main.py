import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.outbox.outbox_processor import OutboxProcessor
from app.outbox.user_event_handler import UserEventHandler
from app.users.api.v1.users import router as users_router_v1
from app.users.db.db_config import create_db_and_tables, db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()

    handlers = [UserEventHandler()]
    processor = OutboxProcessor(db.session_maker, handlers)
    outbox_processor_task = asyncio.create_task(processor.start())
    logger.info("Outbox user service processor started")

    state = {
        "database_ready": True,
        "outbox_processor_ready": True,
    }
    yield state

    if outbox_processor_task:
        await processor.stop()
        await outbox_processor_task


app = FastAPI(lifespan=lifespan)
app.include_router(users_router_v1)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7999, reload=True)
