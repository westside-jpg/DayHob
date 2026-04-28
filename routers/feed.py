from datetime import date
from urllib import request
from fastapi import APIRouter, Request, Form, Depends, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.functions import func
from models import Tasks, Posts, Users, Likes, Comments, Followers
from database import session_factory
from services.dependencies import get_current_user
from services.feed import time_ago, declination_friends, declination_subs, declination_posts, \
    cut_numbers
from fastapi.responses import JSONResponse
from services.cloudinary import upload_avatar

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# == GET-РУЧКИ == #

# Лента
@router.get("/feed", response_class=HTMLResponse)
def feed_page_get(request: Request, current_user = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        task = session.execute(
            select(Tasks).where(Tasks.date == date.today())
        ).scalar_one_or_none()

        likes_subq = (
            select(Likes.post_id, func.count().label("likes_count"))
            .group_by(Likes.post_id)
            .subquery("likes_subq")
        )

        comments_count_subq = (
            select(Comments.post_id, func.count().label("comments_count"))
            .group_by(Comments.post_id)
            .subquery("comments_count_subq")
        )

        is_liked_subq = (
            select(Likes.post_id)
            .where(Likes.user_id == current_user.id)
            .subquery("is_liked_subq")
        )

        rows = session.execute(
            select(Posts, Users, Tasks,
                   func.coalesce(likes_subq.c.likes_count, 0).label("likes_count"),
                   func.coalesce(comments_count_subq.c.comments_count, 0).label("comments_count"),
                   is_liked_subq.c.post_id.isnot(None).label("is_liked"),
                   )
            .join(Users, Posts.user_id == Users.id)
            .join(Tasks, Posts.task_id == Tasks.id)
            .outerjoin(likes_subq, likes_subq.c.post_id == Posts.id)
            .outerjoin(comments_count_subq, comments_count_subq.c.post_id == Posts.id)
            .outerjoin(is_liked_subq, is_liked_subq.c.post_id == Posts.id)
        ).all()

        posts = []
        for post, author, task_i, likes_count, comments_count, is_liked in rows:
            posts.append({
                "id": post.id,
                "created_at": time_ago(post.created_at),
                "image_url": post.image_url,
                "text": post.text,
                "task_id": post.task_id,
                "task_title": task_i.title,
                "author_username": author.username,
                "author_avatar": author.avatar_url,
                "is_liked": is_liked,
                "likes_count": likes_count,
                "comments_count": comments_count
            })

        return templates.TemplateResponse("feed/feed.html", {
            "request": request,
            "task": task,
            "posts": posts,
            "user": current_user,
        })

# Поиск
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
        "results": results
    })

# Логика поиска
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

# Профиль
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
            .subquery("likes_subq")
        )

        comments_count_subq = (
            select(Comments.post_id, func.count().label("comments_count"))
            .group_by(Comments.post_id)
            .subquery("comments_count_subq")
        )

        is_liked_subq = (
            select(Likes.post_id)
            .where(Likes.user_id == current_user.id)
            .subquery("is_liked_subq")
        )

        posts_query = (
            select(
                Posts,
                func.coalesce(likes_subq.c.likes_count, 0).label("likes_count"),
                func.coalesce(comments_count_subq.c.comments_count, 0).label("comments_count"),
                Tasks,
                is_liked_subq.c.post_id.isnot(None).label("is_liked")
            )
            .outerjoin(likes_subq, likes_subq.c.post_id == Posts.id)
            .outerjoin(comments_count_subq, comments_count_subq.c.post_id == Posts.id)
            .join(Tasks, Posts.task_id == Tasks.id)
            .outerjoin(is_liked_subq, is_liked_subq.c.post_id == Posts.id)
            .where(Posts.user_id == profile_user.id)
            .order_by(Posts.created_at.desc())
        )


        rows = session.execute(posts_query).all()

        posts_data = []

        for post, likes_count, comments_count, task_i, is_liked in rows:
            posts_data.append({
                "id": post.id,
                "task_id": post.task_id,
                "task_title": task_i.title,
                "image_url": post.image_url,
                "post_text": post.text,
                "is_liked": is_liked,
                "likes_count": cut_numbers(likes_count),
                "comments_count": cut_numbers(comments_count),
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

        declination = {
            "posts": declination_posts(posts_count),
            "subs": declination_subs(followers_count),
            "friends": declination_friends(friends_count)
        }

        is_subscribed_query = session.execute(
            select(Followers).where(
                Followers.follower_id == current_user.id,
                Followers.following_id == profile_user.id)
        ).scalar_one_or_none()

        if not is_subscribed_query:
            is_subscribed = False
        else:
            is_subscribed = True

        return templates.TemplateResponse("feed/profile.html", {
            "request": request,
            "current_user": current_user,
            "profile_user": profile_user,
            "is_own_profile": is_own_profile,
            "is_subscribed": is_subscribed,
            "posts": posts_data,
            "posts_count": cut_numbers(posts_count),
            "followers_count": cut_numbers(followers_count),
            "friends_count": cut_numbers(friends_count),
            "declination": declination,
        })

@router.get("/post/{post_id}/comments")
def get_comments(post_id: int, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        rows = session.execute(
            select(Comments, Users)
            .join(Users, Comments.user_id == Users.id)
            .where(Comments.post_id == post_id)
            .order_by(Comments.created_at)
        ).all()

        return [
            {
            "comment_username": user.username,
            "comment_avatar_url": user.avatar_url,
            "comment_text": comment.text,
            "comment_created_at": time_ago(comment.created_at)
            }
            for comment, user in rows
        ]

# Настройки
@router.get("/settings")
def get_settings(request: Request, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse("feed/settings.html", {
        "request": request,
        "user": current_user,
    })


# == POST-РУЧКИ == #

# Логика лайка
@router.post("/post/{post_id}/like")
def toggle_like(post_id: int, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        existing = session.execute(
            select(Likes).where(
                Likes.post_id == post_id,
                Likes.user_id == current_user.id
            )
        ).scalar_one_or_none()

        if existing:
            session.delete(existing)
            session.commit()
            liked = False
        else:
            session.add(Likes(post_id=post_id, user_id=current_user.id))
            session.commit()
            liked = True

        count = session.execute(
            select(func.count()).where(Likes.post_id == post_id)
        ).scalar()

    return {"liked": liked, "count": cut_numbers(count)}

# Логика подписки
@router.post("/profile/{username}/follow")
def toggle_subscribe(username: str, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        user = session.execute(
            select(Users).where(Users.username == username)
        ).scalar_one_or_none()

        if not user:
            return {"error": "not found"}

        existing = session.execute(
            select(Followers).where(
                Followers.following_id == user.id,
                Followers.follower_id == current_user.id
            )
        ).scalar_one_or_none()

        if existing:
            session.delete(existing)
            session.commit()
            is_subscribed = False
        else:
            session.add(Followers(following_id=user.id, follower_id=current_user.id))
            session.commit()
            is_subscribed = True

        followers_count = session.execute(
            select(func.count()).where(Followers.following_id == user.id)
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
                    f2.following_id == user.id
                )
            )
            .where(f1.follower_id == user.id)
        ).scalar()

        return {"is_subscribed": is_subscribed,
                "followers_count": cut_numbers(followers_count),
                "declination_subs": declination_subs(followers_count),
                "friends_count": cut_numbers(friends_count),
                "declination_friends": declination_friends(friends_count),
                }

@router.post("/post/{post_id}/post-comment")
def post_comment(post_id: int, text: str = Form(...), current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        session.add(Comments(post_id=post_id, user_id=current_user.id, text=text))
        session.commit()

    return {"ok": True}

@router.post("/settings/apply")
def update_settings(
    bio: str = Form(None),
    avatar: UploadFile = File(None),
    current_user=Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        user = session.execute(
            select(Users).where(Users.username == current_user.username)
        ).scalar_one_or_none()

        user.bio = bio

        if avatar and avatar.filename:
            user.avatar_url = upload_avatar(avatar.file, current_user.username)

        session.commit()
        return {"avatar_url": user.avatar_url, "bio": user.bio}