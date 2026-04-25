from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from pydantic_settings import BaseSettings

class Base(DeclarativeBase):
    pass

class Settings(BaseSettings):
    class config:
        env_file = "postgresql.env"

class Database():
    def __init__(self, settings: Settings):
        self.engine = create_async_engine(
            f"{settings.db_driver}://{settings.db_user}:{settings.db_password}@{settings.db_host}/{settings.db_name}"
        )

        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    def getSession(self) -> AsyncSession:
        return self.session_maker()
    
    async def createTables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)