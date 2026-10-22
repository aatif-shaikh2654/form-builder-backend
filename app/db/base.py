from app.db.database import Base
from app.db.session import engine
import app.models


async def create_base():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)