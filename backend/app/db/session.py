"""
Асинхронное соединение с БД (SQLAlchemy + aiosqlite / asyncpg).

Улучшения:
  - pool_pre_ping=True — автоматически проверяет соединения перед использованием
  - pool_recycle для PostgreSQL — переоткрывает соединения каждые 30 минут
  - Настраиваемый размер пула (только для PostgreSQL — у SQLite нет пула)
  - init_db вынесен в отдельную функцию с явным импортом моделей
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.db.base import Base

_is_sqlite = "sqlite" in settings.DATABASE_URL

# SQLite не поддерживает connection pool — передаём check_same_thread
# PostgreSQL получает pool_size и pool_recycle
_engine_kwargs: dict = {
    "echo": settings.ENV == "development",
    "pool_pre_ping": True,
}

if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20
    _engine_kwargs["pool_recycle"] = 1800  # переоткрываем каждые 30 минут

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,  # объекты остаются доступными после commit
    autoflush=False,          # управляем flush вручную для предсказуемости
)


async def init_db() -> None:
    """
    Создаёт таблицы при первом запуске.
    В production используйте Alembic для миграций.
    """
    # Явно импортируем все модели, чтобы они зарегистрировались в Base.metadata
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Заполняем начальными данными в отдельной транзакции
    async with AsyncSessionLocal() as session:
        from app.db.seed import seed_initial_data
        await seed_initial_data(session)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Depends — провайдер сессии.
    Сессия закрывается автоматически после завершения запроса.
    Rollback при исключении — обрабатывается контекстным менеджером.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
