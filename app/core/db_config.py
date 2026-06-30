from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

Base = declarative_base()


class Database:
    def __init__(self, database_url: str):
        """
        Initialize the Database with an asynchronous engine and session maker.

        Args:
            database_url: URL database
            poolclass: NullPool(we are using pgbouncer)
        """
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            poolclass=NullPool,
        )

        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Generates an asynchronous database session."""
        async with self.session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    async def dispose(self):
        """Close the database engine."""
        await self.engine.dispose()
