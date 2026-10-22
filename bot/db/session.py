"""Подключение к базе данных.

Строка подключения берётся из настроек. Чтобы перейти с SQLite на
PostgreSQL, достаточно поменять DATABASE_URL в .env, например на
postgresql+asyncpg://user:password@host:5432/dbname
(и установить драйвер asyncpg).
"""

from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.db.models import Base


def create_engine(database_url: str) -> AsyncEngine:
    url = make_url(database_url)
    if url.get_backend_name() == "sqlite" and url.database:
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)
    return create_async_engine(database_url)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(engine: AsyncEngine) -> None:
    """Создаёт таблицы, если их ещё нет."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
