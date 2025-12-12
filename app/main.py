import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI

from app.api.v1 import router
from app.db.db_config import create_db_and_tables, get_async_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    state = {"database_ready": True}
    logger.info("Database ready")
    yield state


app = FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7999, reload=True)
