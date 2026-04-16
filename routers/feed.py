from datetime import date
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.functions import func
from models import Tasks, Posts, Users, Likes, Comments, Followers
from database import session_factory
from services.dependencies import get_current_user
from services.feed import time_ago, time_until_next_day
from fastapi.responses import JSONResponse

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

    with session_factory() as session:
        rows = session.execute(
            select(Users).where(Users.username != current_user.username)
        ).scalars().all()

        results = []
        for result in rows:
            results.append({
                "avatar_url": result.avatar_url,
                "username": result.username
            })

    return templates.TemplateResponse("feed/search.html", {
        "request": request,
        "user": current_user,
        "time_until": time_until_next_day(),
        "results": results
    })

@router.get("/search/users")
def search_users(query: str, current_user=Depends(get_current_user)):
    if not current_user:
        return JSONResponse([], status_code=401)

    with session_factory() as session:
        users = session.execute(
            select(Users).where(
                Users.username.ilike(f"%{query}%"),
                Users.username != current_user.username
            )
        ).scalars().all()

        return [{"username": u.username, "avatar_url": u.avatar_url} for u in users]

@router.get("/profile/{username}")
def profile_page_get(request: Request, username: str, current_user = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        # Профиль
        profile_user = session.execute(
            select(Users).where(Users.username == username)
        ).scalar_one_or_none()

        if not profile_user:
            return RedirectResponse("/404", status_code=303)

        # Определение флагов
        is_own_profile = (current_user.id == profile_user.id)
        is_following = False
        if not is_own_profile:
            is_following = session.execute(
                select(Followers).where(
                    Followers.follower_id == current_user.id,
                    Followers.following_id == profile_user.id
                )
            ).scalar_one_or_none() is not None

        # Посты
        likes_subq = (
            select(Likes.post_id, func.count().label("likes_count"))
            .group_by(Likes.post_id)
            .subquery()
        )

        comments_subq = (
            select(Comments.post_id, func.count().label("comments_count"))
            .group_by(Comments.post_id)
            .subquery()
        )

        posts_query = (
            select(
                Posts,
                func.coalesce(likes_subq.c.likes_count, 0).label("likes_count"),
                func.coalesce(comments_subq.c.comments_count, 0).label("comments_count"),
            )
            .outerjoin(likes_subq, likes_subq.c.post_id == Posts.id)
            .outerjoin(comments_subq, comments_subq.c.post_id == Posts.id)
            .where(Posts.user_id == profile_user.id)
            .order_by(Posts.created_at.desc())
        )

        rows = session.execute(posts_query).all()

        posts_data = []

        for post, likes_count, comments_count in rows:
            posts_data.append({
                "task_id": post.task_id,
                "image_url": post.image_url,
                "post_text": post.text,
                "likes_count": likes_count,
                "comments_count": comments_count,
                "created_at": time_ago(post.created_at)
            })

        # Статистика
        posts_count = session.execute(
            select(func.count()).where(Posts.user_id == profile_user.id)
        ).scalar()

        followers_count = session.execute(
            select(func.count()).where(Followers.following_id == profile_user.id)
        ).scalar()

        f1 = aliased(Followers)
        f2 = aliased(Followers)

        friends_count = session.execute(
            select(func.count())
            .select_from(f1)
            .join(
                f2,
                and_(
                    f1.following_id == f2.follower_id,
                    f2.following_id == profile_user.id
                )
            )
            .where(f1.follower_id == profile_user.id)
        ).scalar()

        return templates.TemplateResponse("feed/profile.html", {
            "request": request,
            "current_user": current_user,
            "profile_user": profile_user,
            "is_own_profile": is_own_profile,
            "is_following": is_following,
            "posts": posts_data,
            "posts_count": posts_count,
            "followers_count": followers_count,
            "friends_count": friends_count,
            "time_until": time_until_next_day()
        })