from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Database:
    def __init__(self, database_url: str, echo: bool = False, pool_size: int = 20, max_overflow: int = 10):
        """
        Initialize the Database with an asynchronous engine and session maker.

        Args:
            database_url: URL database
            echo: Log SQL queries if True
            pool_size: Quantity of connections in the pool
            max_overflow: Maximum overflow size of the pool
        """
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
        )

        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_db_and_tables(self, metadata=None):
        """
        Create database tables based on the provided metadata or Base metadata.

        Args:
            metadata: Optional metadata for creating tables
        """
        async with self.engine.begin() as conn:
            if metadata:
                await conn.run_sync(metadata.create_all)
            else:
                await conn.run_sync(Base.metadata.create_all)

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
