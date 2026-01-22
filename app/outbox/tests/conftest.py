# Import fixtures from core - needed for pytest discovery
from app.core.conftest import (  # noqa: F401
    db_session,
    engine,
    event_loop,
    session_maker,
)
