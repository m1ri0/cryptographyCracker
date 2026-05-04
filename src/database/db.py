from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from pydantic_settings import BaseSettings

class Base(DeclarativeBase):
    pass

class Settings(BaseSettings):
    DB_USER: str = "bruteforce"
    DB_PASSWORD: str = "secret"
    DB_HOST: str = "db"
    DB_NAME: str = "hashcracker"
    DB_PORT: str = "5432"
    DB_DRIVER: str = "postgresql+asyncpg"

    class config:
        env_file = ".env"

class Database():
    def __init__(self, settings: Settings):
        self.engine = create_async_engine(
            f"{settings.DB_DRIVER}://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}/{settings.DB_NAME}?port={settings.DB_PORT}"
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