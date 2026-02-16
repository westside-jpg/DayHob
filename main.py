import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database import sync_engine
from models import Base
from routers.auth import router as auth_router

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.include_router(auth_router)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Base.metadata.drop_all(bind=sync_engine)
Base.metadata.create_all(bind=sync_engine)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("auth/index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)