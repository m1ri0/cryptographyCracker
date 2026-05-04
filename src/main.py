import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from database import Database, Settings
from backend.api import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    db = Database(settings)

    await db.createTables()
    app.state.db = db

    yield

    await app.state.db.engine.dispose()

app = FastAPI(lifespan=lifespan, title="Cripto Cracker API")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app", host="0.0.0.0",
        reload=False, port=8000
    )