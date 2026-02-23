from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from services.auth import check_register, register_user, hash_password, verify_login, register_pending_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# == GET-РУЧКИ == #
@router.get("/login", response_class=HTMLResponse)
def login_page_get(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
def register_page_get(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.get("/register/email_verification", response_class=HTMLResponse)
def email_verification_page_get(request: Request):
    return templates.TemplateResponse("auth/email_verification.html", {"request": request})

# == POST-РУЧКИ == #
@router.post("/login", response_class=HTMLResponse)
def login_page_post(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
):
    approve, error = verify_login(username, password)
    if not approve:
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": error, "username": username})
    return templates.TemplateResponse("feed/feed.html", {"request": request})


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

    hashed_password = hash_password(password)
    register_pending_user(username, hashed_password, email_clean)
    return RedirectResponse("/register/email_verification", status_code=303)

@router.post("/register/email_verification", response_class=HTMLResponse)
def email_verification_page_post(request: Request):
    ...
