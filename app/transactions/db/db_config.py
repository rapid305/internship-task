import logging

from app.core.db_config import Database
from app.transactions.settings import settings

logger = logging.getLogger(__name__)

db_url = settings.get("DB.URL")
logger.info(f"DataBaseConnection Url: {db_url}")

db = Database(
    database_url=db_url,
    echo=settings.get("DB.ECHO", settings.get("db.echo", False)),
    pool_size=settings.get("DB.POOL_SIZE", settings.get("db.pool_size", 20)),
    max_overflow=settings.get("DB.MAX_OVERFLOW", settings.get("db.max_overflow", 10)),
)

session_maker = db.session_maker


get_async_session = db.get_async_session
create_db_and_tables = db.create_db_and_tables
