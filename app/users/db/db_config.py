import logging

from sqlalchemy.orm import declarative_base

from app.core.db_config import Database
from app.users.settings import settings

Base = declarative_base()

logger = logging.getLogger(__name__)

settings.setenv("production")

db_url = settings.get("DB.URL") or settings.get("db.url")
logger.info(f"DataBaseConnection Url: {db_url}")

db = Database(
    database_url=db_url,
)

session_maker = db.session_maker

get_async_session = db.get_async_session
