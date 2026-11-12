from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import DATABASE_URL
from typing import Annotated
from sqlalchemy.pool import NullPool
from fastapi import Depends

DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://"
)

engine = create_async_engine(DATABASE_URL,  
    poolclass=NullPool,
    connect_args={
        "statement_cache_size": 0,
        "ssl": "require",
    })

session = async_sessionmaker(bind=engine, class_=AsyncSession, autoflush=False, expire_on_commit=False)


async def get_db():
    db = session()
    try:
        yield db
    except:
        await db.rollback()
        raise
    finally:
        await db.close()

DbSession = Annotated[AsyncSession, Depends(get_db)]