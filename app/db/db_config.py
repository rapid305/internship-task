from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
import typing
from app.settings import settings

DATABASE_URL = settings.db.url

Base = declarative_base()

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False , autocommit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> typing.AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session