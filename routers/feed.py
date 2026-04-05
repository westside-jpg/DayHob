from datetime import date
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from models import Tasks, Posts, Users
from database import session_factory
from services.dependencies import get_current_user
from services.feed import time_ago, time_until_next_day

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# == GET-РУЧКИ == #
@router.get("/feed", response_class=HTMLResponse)
def feed_page_get(request: Request, current_user = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        task = session.execute(
            select(Tasks).where(Tasks.date == date.today())
        ).scalar_one_or_none()

        rows = session.execute(
            select(Posts, Users).join(Users, Posts.user_id == Users.id)
        ).all()

        posts = []
        for post, author in rows:
            posts.append({
                "id": post.id,
                "created_at": time_ago(post.created_at),
                "image_url": post.image_url,
                "text": post.text,
                "task_id": post.task_id,
                "author_username": author.username,
                "author_avatar": author.avatar_url,
                "likes_count": 0,
                "comments_count": 0
            })

        return templates.TemplateResponse("feed/feed.html", {
            "request": request,
            "task": task,
            "posts": posts,
            "user": current_user,
            "time_until": time_until_next_day()
        })

@router.get("/search", response_class=HTMLResponse)
def search_page_get(request: Request, current_user = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse("feed/search.html", {
        "request": request,
        "user": current_user,
        "time_until": time_until_next_day()
    })