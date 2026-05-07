from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from fastapi import FastAPI, Request
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
    await app.state.db.async_engine.dispose()

app = FastAPI(lifespan=lifespan, title="Cripto Cracker API")

templates = Jinja2Templates(directory="client")
app.mount("/static", StaticFiles(directory="client/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    context = {
        "title": "Cripto Cracker Dashboard",
        "status": "System is operational"
    }

    return templates.TemplateResponse(request=request, name="index.html", context=context)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app", host="0.0.0.0",
        reload=False, port=8000
    )