from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from services.dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# == GET-РУЧКИ == #
@router.get("/feed", response_class=HTMLResponse)
def feed_page_get(request: Request, current_user = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse("feed/feed.html", {
        "request": request,
        "user": current_user
    })