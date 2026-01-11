import logging

from app.core.db_config import Database
from app.users.settings import settings

logger = logging.getLogger(__name__)

logger.info(f"DataBaseConnection Url: {settings.db.url}")

db = Database(
    database_url=settings.db.url,
    echo=settings.get("db.echo", False),
    pool_size=settings.get("db.pool_size", 20),
    max_overflow=settings.get("db.max_overflow", 10),
)

session_maker = db.session_maker

get_async_session = db.get_async_session
create_db_and_tables = db.create_db_and_tables
