from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

class Base(DeclarativeBase):
    pass

class Settings(BaseSettings):
    DB_USER: str = "bruteforce"
    DB_PASSWORD: str = "secret"
    DB_HOST: str = "db"
    DB_NAME: str = "hashcracker"
    DB_PORT: str = "5432"
    DB_ASYNC_DRIVER: str = "postgresql+asyncpg"
    DB_SYNC_DRIVER: str = "postgresql+psycopg2"

    class config:
        env_file = ".env"

class Database():
    def __init__(self, settings: Settings):
        self.engine = create_engine(
            f"{settings.DB_SYNC_DRIVER}://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}/{settings.DB_NAME}?port={settings.DB_PORT}"
        )

        self.async_engine = create_async_engine(
            f"{settings.DB_ASYNC_DRIVER}://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}/{settings.DB_NAME}?port={settings.DB_PORT}"
        )

        self.session_maker = sessionmaker(
            bind=self.engine,
            expire_on_commit=False
        )

        self.async_session_maker = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    def getAsyncSession(self) -> AsyncSession:
        return self.async_session_maker()
    
    def getSession(self):
        return self.session_maker()
    
    async def createTables(self):
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)