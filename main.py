import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database import async_engine, session_factory
from models import Base, PendingUsers
from routers.auth import router as auth_router
from routers.feed import router as feed_router
from rich.logging import RichHandler
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone, timedelta
from sqlalchemy import delete

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def clean_pending_users():
    async with session_factory() as session:
        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        await session.execute(
            delete(PendingUsers).where(PendingUsers.created_at < expired)
        )
        await session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(clean_pending_users, 'interval', hours=1)
    scheduler.start()

    yield

    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
app.include_router(auth_router)
app.include_router(feed_router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "errors/error-404.html",
        {"request": request},
        status_code=404
    )

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "auth/index.html",
        {"request": request}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, use_colors=True)