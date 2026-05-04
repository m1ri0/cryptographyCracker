import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from database import Database, Settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    database = Database(settings)

    await database.createTables()
    app.state.db = database

    yield

    await app.state.db.engine.dispose()

if __name__ == "__main__":
    uvicorn.run(
        "main:app", host="0.0.0.0",
        reload=False, port=8000
    )