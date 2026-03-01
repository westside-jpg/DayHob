from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from services.auth import check_register, hash_password, verify_login, register_pending_user, \
    send_verification_email, check_verification_email_and_register
from services.auth_jwt import create_access_token

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
def email_verification_page_get(request: Request, email: str):
    return templates.TemplateResponse("auth/email_verification.html", {"request": request, "email": email})

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

    token = create_access_token(username)

    redirect = RedirectResponse("/feed", status_code=303)

    redirect.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=30 * 24 * 60 * 60
    )

    return redirect


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
    code = register_pending_user(username, hashed_password, email_clean)
    send_verification_email(email_clean, code)
    return RedirectResponse(f"/register/email_verification?email={email_clean}", status_code=303)

@router.post("/register/email_verification", response_class=HTMLResponse)
def email_verification_page_post(request: Request,
                                 code: str = Form(...),
                                 email: str = Form(...)):

    approve, error = check_verification_email_and_register(email, code)

    if not approve:
        return templates.TemplateResponse("auth/email_verification.html", {"request": request, "error": error, "email": email})

    return templates.TemplateResponse("auth/login.html", {"request": request})
