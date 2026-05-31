import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database import sync_engine
from models import Base
from routers.auth import router as auth_router
from routers.feed import router as feed_router
from rich.logging import RichHandler
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from database import session_factory
from models import PendingUsers
from datetime import datetime, timezone, timedelta

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.include_router(auth_router)
app.include_router(feed_router)
app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.drop_all(bind=sync_engine)
Base.metadata.create_all(bind=sync_engine)

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)

def clean_pending_users():
    with session_factory() as session:
        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        session.query(PendingUsers).filter(PendingUsers.created_at < expired).delete()
        session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(clean_pending_users, 'interval', hours=1)
scheduler.start()

@app.exception_handler(404)
def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "errors/error-404.html",
        {"request": request},
        status_code=404
    )

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "auth/index.html",
        {"request": request}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, use_colors=True)