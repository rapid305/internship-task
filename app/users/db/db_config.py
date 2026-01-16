import logging

from app.core.db_config import Database
from app.users.settings import settings

logger = logging.getLogger(__name__)

db_url = settings.get("DB.URL")
logger.info(f"Database URL: {db_url}")

db = Database(
    database_url=db_url,
    echo=settings.get("DB.ECHO", False),
    pool_size=settings.get("DB.POOL_SIZE"),
    max_overflow=settings.get("DB.MAX_OVERFLOW"),
    pool_recycle=settings.get("DB.POOL_RECYCLE"),
)

session_maker = db.session_maker
get_async_session = db.get_async_session
create_db_and_tables = db.create_db_and_tables
