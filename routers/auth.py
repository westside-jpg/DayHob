from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from services.auth import check_register, register_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
def login_page_get(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
def register_page_get(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
def login_page_post(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
):
    ...

@router.post("/register", response_class=HTMLResponse)
def register_page_post(
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        password_confirm: str = Form(...),
):
    errors, username_clean, email_clean = check_register(
        username, email, password, password_confirm
    )

    if errors:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "errors": errors,
                "username": username,
                "email": email
            }
        )

    register_user(username_clean, email_clean, password)
    return templates.TemplateResponse("feed/feed.html", {"request": request})