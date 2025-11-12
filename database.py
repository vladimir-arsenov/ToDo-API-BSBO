from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
from uuid import uuid4
import os
from dotenv import load_dotenv

# Попытка импорта моделей
try:
    from models import Base, Task
except ImportError:
    class Base(DeclarativeBase):
        pass

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# ИСПРАВЛЕННАЯ КОНФИГУРАЦИЯ для работы с pgBouncer
engine = create_async_engine(
    DATABASE_URL,
    # Используем стандартный пулинг вместо NullPool
    pool_size=10,               # Количество постоянных соединений
    max_overflow=5,             # Дополнительные соединения при нагрузке
    pool_timeout=30,            # Таймаут ожидания соединения (секунды)
    pool_recycle=1800,          # Переиспользовать соединения каждые 30 минут (1800 сек)
    pool_pre_ping=True,         # ВАЖНО: Проверять соединение перед использованием
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
        "command_timeout": 60,   # Таймаут команды (секунды)
        "server_settings": {
            "jit": "off",        # Отключаем JIT для стабильности
        }
    },
    echo=False
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False
)


async def init_db():
    """
    Создание таблиц в БД.
    ВНИМАНИЕ: Из-за проблем с pgBouncer рекомендуется создавать таблицы
    через Supabase SQL Editor вручную.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ База данных инициализирована!")


async def drop_db():
    """Удаление всех таблиц"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("⚠️ Все таблицы удалены!")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии БД в эндпоинтах"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
