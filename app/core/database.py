# app/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlmodel import SQLModel

from app.core.config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True,echo=True)
Base = declarative_base()

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)



async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
