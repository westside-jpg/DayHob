import asyncio
import json
from datetime import date
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import and_, update, asc
from sqlalchemy.sql.functions import func
from models import Tasks, Posts, Users, Likes, Comments, Followers, Pushes, PushType, Messages
from database import session_factory
from services.dependencies import get_current_user
from services.feed import time_ago, declination_friends, declination_subs, declination_posts, \
    cut_numbers, declination_pushes, cut_text, delete_old_pushes, cut_pushes_count, unread_pushes_count_func, \
    declination_following, declination_messages, format_time_H_M, unread_messages_count_func
from fastapi.responses import JSONResponse
from services.cloudinary_func import upload_avatar, delete_avatar
from services.websocket_manager import manager

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# == GET-РУЧКИ == #

# Лента
@router.get("/feed", response_class=HTMLResponse)
async def feed_page_get(request: Request, current_user = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        task_Q = await session.execute(
            select(Tasks).where(Tasks.date == date.today())
        )

        task = task_Q.scalar_one_or_none()

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

        rows_Q = await session.execute(
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
        )

    rows = rows_Q.all()

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

    unread_pushes_count = await unread_pushes_count_func(current_user)
    unread_messages_count = await unread_messages_count_func(current_user)

    return templates.TemplateResponse("feed/feed.html", {
        "request": request,
        "task": task,
        "posts": posts,
        "current_user": current_user,
        "unread_pushes_count": cut_pushes_count(unread_pushes_count),
        "unread_messages_count": cut_numbers(unread_messages_count),
    })

# Поиск людей
@router.get("/search", response_class=HTMLResponse)
async def search_page_users_get(request: Request, current_user = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        rows_Q = await session.execute(
            select(Users).where(Users.username != current_user.username)
        )

        rows = rows_Q.scalars().all()

    results = []
    for result in rows:
        results.append({
            "avatar_url": result.avatar_url,
            "username": result.username
        })

    unread_pushes_count = await unread_pushes_count_func(current_user)
    unread_messages_count = await unread_messages_count_func(current_user)

    return templates.TemplateResponse("feed/search.html", {
        "request": request,
        "current_user": current_user,
        "results": results,
        "unread_pushes_count": cut_pushes_count(unread_pushes_count),
        "unread_messages_count": cut_numbers(unread_messages_count),
    })

# Логика поиска людей
@router.get("/search/users")
async def search_users(query: str, current_user=Depends(get_current_user)):
    if not current_user:
        return JSONResponse([], status_code=401)

    async with session_factory() as session:
        users_Q = await session.execute(
            select(Users).where(
                Users.username.ilike(f"%{query}%"),
                Users.username != current_user.username
            )
        )

        users = users_Q.scalars().all()

        return [{"username": u.username, "avatar_url": u.avatar_url} for u in users]

# Логика поиска постов
@router.get("/search/posts")
async def search_posts(query: str = "", current_user=Depends(get_current_user)):
    if not current_user:
        return JSONResponse([], status_code=401)

    q = query.strip()

    async with session_factory() as session:
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

        stmt = (
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
        )

        if len(q) >= 2:
            stmt = stmt.where(func.lower(Posts.text).contains(q.lower()))

        rows_Q = await session.execute(
            stmt.order_by(Posts.created_at.desc()).limit(30)
        )

        rows = rows_Q.all()

    posts = []
    for post, author, task_i, likes_count, comments_count, is_liked in rows:
        posts.append({
            "id": post.id,
            "created_at": time_ago(post.created_at),
            "image_url": post.image_url,
            "text": post.text,
            "task_title": task_i.title,
            "author_username": author.username,
            "author_avatar": author.avatar_url,
            "is_liked": is_liked,
            "likes_count": cut_numbers(likes_count),
            "comments_count": cut_numbers(comments_count),
            "current_user": current_user,
        })

    return posts

# Профиль
@router.get("/profile/{username}")
async def profile_page_get(request: Request, username: str, current_user = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        # Профиль
        profile_user_Q = await session.execute(
            select(Users).where(Users.username == username)
        )

        profile_user = profile_user_Q.scalar_one_or_none()

        if not profile_user:
            return RedirectResponse("/404", status_code=303)

        is_own_profile = (current_user.id == profile_user.id)

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


        rows_Q = await session.execute(posts_query)
        rows = rows_Q.all()

        posts_data = []

        for post, likes_count, comments_count, task_i, is_liked in rows:
            posts_data.append({
                "id": post.id,
                "author_username": profile_user.username,
                "author_avatar": profile_user.avatar_url,
                "task_id": post.task_id,
                "task_title": task_i.title,
                "image_url": post.image_url,
                "post_text": post.text,
                "is_liked": is_liked,
                "text": post.text,
                "likes_count": cut_numbers(likes_count),
                "comments_count": cut_numbers(comments_count),
                "created_at": time_ago(post.created_at)
            })

        # Статистика
        posts_count_Q = await session.execute(
            select(func.count()).select_from(Posts).where(Posts.user_id == profile_user.id)
        )

        posts_count = posts_count_Q.scalar()

        followers_count_Q = await session.execute(
            select(func.count()).select_from(Followers).where(Followers.following_id == profile_user.id)
        )

        followers_count = followers_count_Q.scalar()

        f1 = aliased(Followers)
        f2 = aliased(Followers)

        friends_count_Q = await session.execute(
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
        )

        friends_count = friends_count_Q.scalar()

        following_count_Q = await session.execute(
            select(func.count())
            .select_from(Followers)
            .where(Followers.follower_id == profile_user.id)
        )

        following_count = following_count_Q.scalar()

        declination = {
            "posts": declination_posts(posts_count),
            "subs": declination_subs(followers_count),
            "friends": declination_friends(friends_count),
            "following": declination_following(following_count)
        }

        is_subscribed_query_Q = await session.execute(
            select(Followers).where(
                Followers.follower_id == current_user.id,
                Followers.following_id == profile_user.id)
        )

        is_subscribed_query = is_subscribed_query_Q.scalar_one_or_none()

        if not is_subscribed_query:
            is_subscribed = False
        else:
            is_subscribed = True

        unread_pushes_count = await unread_pushes_count_func(current_user)
        unread_messages_count = await unread_messages_count_func(current_user)

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
            "following_count": cut_numbers(following_count),
            "declination": declination,
            "unread_pushes_count": cut_pushes_count(unread_pushes_count),
            "unread_messages_count": cut_pushes_count(unread_messages_count),
        })

@router.get("/post/{post_id}/comments")
async def get_comments(post_id: int, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        post_Q = await session.execute(
            select(Posts)
            .where(Posts.id == post_id)
        )

        post = post_Q.scalar_one_or_none()

        if not post:
            return {"error": "Пост не найден"}

        rows_Q = await session.execute(
            select(Comments, Users)
            .join(Users, Comments.user_id == Users.id)
            .where(Comments.post_id == post_id)
            .order_by(Comments.created_at)
        )

        rows = rows_Q.all()

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
async def get_settings(request: Request, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    unread_pushes_count = await unread_pushes_count_func(current_user)
    unread_messages_count = await unread_messages_count_func(current_user)

    return templates.TemplateResponse("feed/settings.html", {
        "request": request,
        "current_user": current_user,
        "unread_pushes_count": cut_pushes_count(unread_pushes_count),
        "unread_messages_count": cut_pushes_count(unread_messages_count),
    })

# Друзья
@router.get("/friends")
async def get_friends(request: Request, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        f1 = aliased(Followers)
        f2 = aliased(Followers)

        friends_count_Q = await session.execute(
            select(func.count())
            .select_from(f1)
            .join(f2, and_(
                f1.following_id == f2.follower_id,
                f2.following_id == current_user.id
            ))
            .where(f1.follower_id == current_user.id)
        )

        friends_count = friends_count_Q.scalar()

        friends_ids_Q = await session.execute(
            select(f1.following_id)
            .join(f2, and_(
                f1.following_id == f2.follower_id,
                f2.following_id == current_user.id
            ))
            .where(f1.follower_id == current_user.id)
        )

        friends_ids = friends_ids_Q.scalars().all()

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

        rows_Q = await session.execute(
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
            .where(Posts.user_id.in_(friends_ids))
            .order_by(Posts.created_at.desc())
        )

        rows = rows_Q.all()

        posts = []
        for post, author, task, likes_count, comments_count, is_liked in rows:
            posts.append({
                "id": post.id,
                "author_username": author.username,
                "author_avatar": author.avatar_url,
                "task_title": task.title,
                "created_at": time_ago(post.created_at),
                "image_url": post.image_url,
                "text": post.text,
                "likes_count": cut_numbers(likes_count),
                "comments_count": cut_numbers(comments_count),
                "is_liked": is_liked,
            })

        unread_pushes_count = await unread_pushes_count_func(current_user)
        unread_messages_count = await unread_messages_count_func(current_user)

        return templates.TemplateResponse("feed/friends.html", {
            "request": request,
            "posts": posts,
            "current_user": current_user,
            "friends_count": friends_count,
            "friends_declination": declination_friends(friends_count),
            "unread_pushes_count": cut_pushes_count(unread_pushes_count),
            "unread_messages_count": cut_pushes_count(unread_messages_count),
        })

# Пуши
@router.get("/push")
async def get_push(request: Request, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        push_count_Q = await session.execute(
            select(func.count()).select_from(Pushes)
            .where(Pushes.user_id == current_user.id, Pushes.is_read == False)
        )

        push_count = push_count_Q.scalar()

        unread_pushes_Q = await session.execute(
            select(Pushes, Users)
            .outerjoin(Users, Pushes.sender_id == Users.id)
            .where(Pushes.user_id == current_user.id, Pushes.is_read == False)
            .order_by(Pushes.created_at.desc())
        )

        unread_pushes = unread_pushes_Q.all()

        read_pushes_Q = await session.execute(
            select(Pushes, Users)
            .outerjoin(Users, Pushes.sender_id == Users.id)
            .where(Pushes.user_id == current_user.id, Pushes.is_read == True)
            .order_by(Pushes.created_at.desc())
        )

        read_pushes = read_pushes_Q.all()

        pushes_unread = []
        pushes_read = []

        for push, avatar in unread_pushes:
            pushes_unread.append({
                "sender_avatar_url": avatar.avatar_url,
                "sender_username": avatar.username,
                "created_at": time_ago(push.created_at),
                "text": push.text
            })

        for push, avatar in read_pushes:
            pushes_read.append({
                "sender_avatar_url": avatar.avatar_url,
                "sender_username": avatar.username,
                "created_at": time_ago(push.created_at),
                "text": push.text
            })

        await session.execute(
            update(Pushes)
            .where(Pushes.user_id == current_user.id, Pushes.is_read == False)
            .values(is_read=True)
        )

        await session.commit()

        return templates.TemplateResponse("feed/push.html", {
            "request": request,
            "current_user": current_user,
            "push_count": push_count,
            "push_declination": declination_pushes(push_count),
            "pushes_unread": pushes_unread,
            "pushes_read": pushes_read,
        })


# Список друзей пользователя
@router.get("/profile/{username}/friends_list")
async def get_friends_list(request: Request, username: str, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        user_Q = await session.execute(
            select(Users).where(Users.username == username)
        )

        user = user_Q.scalar_one_or_none()

        if not user:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JSONResponse({"error": "Пользователь не найден"}, status_code=404)
            return RedirectResponse("/404", status_code=303)

        f1 = aliased(Followers)
        f2 = aliased(Followers)

        friends_count_Q = await session.execute(
            select(func.count())
            .select_from(f1)
            .join(f2, and_(
                f1.following_id == f2.follower_id,
                f2.following_id == current_user.id
            ))
            .where(f1.follower_id == current_user.id)
        )

        friends_count = friends_count_Q.scalar()

        friends_ids_Q = await session.execute(
            select(f1.following_id)
            .join(f2, and_(
                f1.following_id == f2.follower_id,
                f2.following_id == user.id
            ))
            .where(f1.follower_id == user.id)
        )

        friends_ids = friends_ids_Q.scalars().all()

        rows_Q = await session.execute(
            select(Users)
            .where(Users.id.in_(friends_ids))
        )

        rows = rows_Q.scalars().all()

        results = []

        for result in rows:
            results.append({
                "username": result.username,
                "avatar_url": result.avatar_url,
            })

        unread_pushes_count = await unread_pushes_count_func(current_user)
        unread_messages_count = await unread_messages_count_func(current_user)

        return templates.TemplateResponse("feed/users-list.html", {
            "request": request,
            "current_user": current_user,
            "count": friends_count,
            "declination": declination_friends(friends_count),
            "results": results,
            "unread_pushes_count": cut_pushes_count(unread_pushes_count),
            "unread_messages_count": cut_pushes_count(unread_messages_count),
        })


# Список подписчиков пользователя
@router.get("/profile/{username}/subs_list")
async def get_subs_list(request: Request, username: str, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        user_Q = await session.execute(
            select(Users).where(Users.username == username)
        )

        user = user_Q.scalar_one_or_none()

        if not user:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JSONResponse({"error": "Пользователь не найден"}, status_code=404)
            return RedirectResponse("/404", status_code=303)

        subs_count_Q = await session.execute(
            select(func.count())
            .select_from(Followers)
            .where(Followers.following_id == user.id)
        )

        subs_count = subs_count_Q.scalar()

        subs_ids_Q = await session.execute(
            select(Followers.follower_id)
            .where(Followers.following_id == user.id)
        )

        subs_ids = subs_ids_Q.scalars().all()

        rows_Q = await session.execute(
            select(Users)
            .where(Users.id.in_(subs_ids))
        )

        rows = rows_Q.scalars().all()

        results = []

        for result in rows:
            results.append({
                "username": result.username,
                "avatar_url": result.avatar_url,
            })

        unread_pushes_count = await unread_pushes_count_func(current_user)
        unread_messages_count = await unread_messages_count_func(current_user)

        return templates.TemplateResponse("feed/users-list.html", {
            "request": request,
            "current_user": current_user,
            "count": subs_count,
            "declination": declination_subs(subs_count),
            "results": results,
            "unread_pushes_count": cut_pushes_count(unread_pushes_count),
            "unread_messages_count": cut_pushes_count(unread_messages_count),
        })

# Список подписок пользователя
@router.get("/profile/{username}/following_list")
async def get_following_list(request: Request, username: str, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        user_Q = await session.execute(
            select(Users).where(Users.username == username)
        )

        user = user_Q.scalar_one_or_none()

        if not user:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JSONResponse({"error": "Пользователь не найден"}, status_code=404)
            return RedirectResponse("/404", status_code=303)

        following_count_Q = await session.execute(
            select(func.count())
            .select_from(Followers)
            .where(Followers.follower_id == user.id)
        )

        following_count = following_count_Q.scalar()

        following_ids_Q = await session.execute(
            select(Followers.following_id)
            .where(Followers.follower_id == user.id)
        )

        following_ids = following_ids_Q.scalars().all()

        rows_Q = await session.execute(
            select(Users)
            .where(Users.id.in_(following_ids))
        )

        rows = rows_Q.scalars().all()

        results = []

        for result in rows:
            results.append({
                "username": result.username,
                "avatar_url": result.avatar_url,
            })

        unread_pushes_count = await unread_pushes_count_func(current_user)
        unread_messages_count = await unread_messages_count_func(current_user)

        return templates.TemplateResponse("feed/users-list.html", {
            "request": request,
            "current_user": current_user,
            "count": following_count,
            "declination": declination_following(following_count),
            "results": results,
            "unread_pushes_count": cut_pushes_count(unread_pushes_count),
            "unread_messages_count": cut_pushes_count(unread_messages_count),
        })

# Список чатов
@router.get("/chats")
async def get_chats(request: Request, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        sent_ids_Q = await session.execute(
            select(Messages.receiver_id)
            .where(Messages.sender_id == current_user.id)
        )

        sent_ids = sent_ids_Q.scalars().all()

        received_ids_Q = await session.execute(
            select(Messages.sender_id)
            .where(Messages.receiver_id == current_user.id)
        )

        received_ids = received_ids_Q.scalars().all()

        companion_ids = set(sent_ids + received_ids)

        results = []
        for companion_id in companion_ids:
            companion = await session.get(Users, companion_id)

            messages_count_Q = await session.execute(
                select(func.count())
                .select_from(Messages)
                .where(
                    Messages.sender_id == companion_id,
                    Messages.receiver_id == current_user.id,
                    Messages.is_read == False
                )
            )

            messages_count = messages_count_Q.scalar()

            results.append({
                "username": companion.username,
                "avatar_url": companion.avatar_url,
                "messages_count": cut_pushes_count(messages_count),
            })

        total_unread_Q = await session.execute(
            select(func.count())
            .select_from(Messages)
            .where(
                Messages.receiver_id == current_user.id,
                Messages.is_read == False
            )
        )

        total_unread = total_unread_Q.scalar()

        unread_pushes_count = await unread_pushes_count_func(current_user)

    return templates.TemplateResponse("feed/users-list.html", {
        "request": request,
        "current_user": current_user,
        "results": results,
        "count": total_unread,
        "declination": declination_messages(total_unread),
        "unread_pushes_count": cut_pushes_count(unread_pushes_count),
        "chats": True,
    })

@router.get("/chats/{username}")
async def get_chat_with_user(username: str, request: Request, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        companion_Q = await session.execute(
            select(Users)
            .where(Users.username == username)
        )

        companion = companion_Q.scalar()

        companion_messages_query_Q = await session.execute(
            select(Messages)
            .where(Messages.sender_id == companion.id, Messages.receiver_id == current_user.id)
            .order_by(asc(Messages.created_at))
        )

        companion_messages_query = companion_messages_query_Q.scalars().all()

        user_messages_query_Q = await session.execute(
            select(Messages)
            .where(Messages.sender_id == current_user.id, Messages.receiver_id == companion.id)
            .order_by(asc(Messages.created_at))
        )

        user_messages_query = user_messages_query_Q.scalars().all()

        all_messages = []

        for message in user_messages_query:
            all_messages.append({
                "text": message.text,
                "time": format_time_H_M(message.created_at),
                "created_at": message.created_at,
                "is_mine": True
            })

        for message in companion_messages_query:
            all_messages.append({
                "text": message.text,
                "time": format_time_H_M(message.created_at),
                "created_at": message.created_at,
                "is_mine": False
            })

        all_messages.sort(key=lambda m: m["created_at"])

        unread_pushes_count = await unread_pushes_count_func(current_user)

        await session.execute(
            update(Messages)
            .where(
                Messages.sender_id == companion.id,
                Messages.receiver_id == current_user.id,
                Messages.is_read == False
            )
            .values(is_read=True)
        )

        await session.commit()

    return templates.TemplateResponse("feed/chats.html", {
        "all_messages": all_messages,
        "companion": companion,
        "request": request,
        "current_user": current_user,
        "unread_pushes_count": cut_pushes_count(unread_pushes_count),
        "chats": True,
    })

# == POST-РУЧКИ == #

# Логика лайка
@router.post("/post/{post_id}/like")
async def toggle_like(post_id: int, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        post_Q = await session.execute(
            select(Posts)
            .where(Posts.id == post_id)
        )

        post = post_Q.scalar_one_or_none()

        if not post:
            return {"ok": False, "error": "Пост не найден"}

        existing_Q = await session.execute(
            select(Likes).where(
                Likes.post_id == post_id,
                Likes.user_id == current_user.id
            )
        )

        existing = existing_Q.scalar_one_or_none()

        if existing:
            await session.delete(existing)

            if post.user_id != current_user.id:
                push_Q = await session.execute(
                    select(Pushes)
                    .where(
                        Pushes.post_id == post_id,
                        Pushes.type == PushType.LIKE,
                        Pushes.user_id == post.user_id,
                        Pushes.sender_id == current_user.id
                    )
                )

                push = push_Q.scalar_one_or_none()

                if push:
                    await session.delete(push)

            await session.commit()
            liked = False
        else:
            session.add(Likes(post_id=post_id, user_id=current_user.id))
            if post.user_id != current_user.id:
                session.add(Pushes(
                        user_id=post.user_id,
                        sender_id=current_user.id,
                        text=f"Лайкнул Ваш пост \"{cut_text(post.text)}\"",
                        post_id=post_id,
                        type=PushType.LIKE,
                        is_read=False,
                    )
                )
                await delete_old_pushes(post.user_id)
            await session.commit()
            liked = True

        count_Q = await session.execute(
            select(func.count())
            .select_from(Likes)
            .where(Likes.post_id == post_id)
        )

        count = count_Q.scalar()

    return {"ok": True, "liked": liked, "count": cut_numbers(count)}

# Логика подписки
@router.post("/profile/{username}/follow")
async def toggle_subscribe(username: str, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        user_Q = await session.execute(
            select(Users).where(Users.username == username)
        )
        user = user_Q.scalar_one_or_none()

        if not user:
            return {"ok": False, "error": "Пользователь не найден"}

        existing_Q = await session.execute(
            select(Followers).where(
                Followers.following_id == user.id,
                Followers.follower_id == current_user.id
            )
        )
        existing = existing_Q.scalar_one_or_none()

        # Проверяем подписан ли user на current_user
        reverse_Q = await session.execute(
            select(Followers).where(
                Followers.following_id == current_user.id,
                Followers.follower_id == user.id
            )
        )

        reverse = reverse_Q.scalar_one_or_none()

        if existing:
            await session.delete(existing)

            push_sub_Q = await session.execute(
                select(Pushes)
                .where(
                    Pushes.user_id == user.id,
                    Pushes.sender_id == current_user.id,
                    Pushes.type == PushType.FOLLOW,
                )
            )

            push_sub = push_sub_Q.scalar_one_or_none()

            if push_sub:
                await session.delete(push_sub)

            if reverse:
                push_fri_1_Q = await session.execute(
                    select(Pushes)
                    .where(
                        Pushes.user_id == user.id,
                        Pushes.sender_id == current_user.id,
                        Pushes.type == PushType.FRIENDS,
                    )
                )

                push_fri_1 = push_fri_1_Q.scalar_one_or_none()

                push_fri_2_Q = await session.execute(
                    select(Pushes)
                    .where(
                        Pushes.user_id == current_user.id,
                        Pushes.sender_id == user.id,
                        Pushes.type == PushType.FRIENDS,
                    )
                )
                push_fri_2 = push_fri_2_Q.scalar_one_or_none()

                if push_fri_1:
                    await session.delete(push_fri_1)

                if push_fri_2:
                    await session.delete(push_fri_2)

            await session.commit()
            is_subscribed = False
        else:
            session.add(Followers(following_id=user.id, follower_id=current_user.id))

            session.add(Pushes(
                user_id=user.id,
                sender_id=current_user.id,
                text=f"Подписался на Вас",
                is_read=False,
                type=PushType.FOLLOW,
            ))
            await delete_old_pushes(user.id)

            if reverse:
                session.add(Pushes(
                    user_id=user.id,
                    sender_id=current_user.id,
                    text=f"Теперь Ваш друг",
                    is_read=False,
                    type=PushType.FRIENDS,
                ))
                await delete_old_pushes(user.id)

                session.add(Pushes(
                    user_id=current_user.id,
                    sender_id=user.id,
                    text=f"Теперь Ваш друг",
                    is_read=False,
                    type=PushType.FRIENDS,
                ))
                await delete_old_pushes(current_user.id)

            await session.commit()
            is_subscribed = True

        followers_count_Q = await session.execute(
            select(func.count()).select_from(Followers).where(Followers.following_id == user.id)
        )

        followers_count = followers_count_Q.scalar()

        f1 = aliased(Followers)
        f2 = aliased(Followers)

        friends_count_Q = await session.execute(
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
        )
        friends_count = friends_count_Q.scalar()

        unread_pushes_count = await unread_pushes_count_func(current_user)

        return {"ok": True,
                "is_subscribed": is_subscribed,
                "followers_count": cut_numbers(followers_count),
                "declination_subs": declination_subs(followers_count),
                "friends_count": cut_numbers(friends_count),
                "declination_friends": declination_friends(friends_count),
                "unread_pushes_count": cut_pushes_count(unread_pushes_count)
                }

# Логика публикации коммента
@router.post("/post/{post_id}/post-comment")
async def post_comment(post_id: int, text: str = Form(...), current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    if len(text) > 500:
        return {"error": "Длина комментария больше 500 символов"}

    async with session_factory() as session:
        post_Q = await session.execute(
            select(Posts)
            .where(Posts.id == post_id)
        )
        post = post_Q.scalar_one_or_none()

        if not post:
            return {"error": "Пост не найден"}

        session.add(Comments(
            post_id=post_id,
            user_id=current_user.id,
            text=text
        ))

        if post.user_id != current_user.id:
            session.add(Pushes(
                user_id=post.user_id,
                sender_id=current_user.id,
                post_id = post_id,
                text=f"Написал комментарий к вашему посту \"{cut_text(post.text)}\": \"{cut_text(text)}\"",
                is_read=False,
                type=PushType.COMMENT,
            ))
            await delete_old_pushes(post.user_id)
        await session.commit()

    return {"ok": True}

# Ручка обновления настроек
@router.post("/settings/apply")
async def update_settings(
    bio: str = Form(None),
    avatar: UploadFile = File(None),
    current_user=Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    if bio is not None and len(bio) > 150:
        return {"error": "Максимальная длина описания профиля — 150 символов"}

    async with session_factory() as session:
        user_Q = await session.execute(
            select(Users).where(Users.username == current_user.username)
        )
        user = user_Q.scalar_one_or_none()

        if not user:
            return {"error": "Пользователя не существует"}

        user.bio = bio

        if avatar and avatar.filename:
            loop = asyncio.get_running_loop()
            user.avatar_url = await loop.run_in_executor(
                None,
                upload_avatar,
                avatar.file,
                current_user.username
            )

        await session.commit()
        return {"avatar_url": user.avatar_url, "bio": user.bio}

# Ручка удаления поста
@router.post("/post/{post_id}/delete")
async def delete_post(post_id: int, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    async with session_factory() as session:
        post_Q = await session.execute(
            select(Posts)
            .where(Posts.id == post_id)
        )

        post = post_Q.scalar_one_or_none()

        if not post:
            return {"error": "Ошибка удаления"}

        if post.user_id != current_user.id:
            return {"error": "У Вас нет прав удалить этот пост"}

        await session.delete(post)
        await session.commit()

        posts_count_Q = await session.execute(
            select(func.count()).select_from(Posts)
            .where(Posts.user_id == current_user.id)
        )
        posts_count = posts_count_Q.scalar()

        return {"ok": True,
                "message": "Ваш пост был успешно удален",
                "count": posts_count,
                "declination": declination_posts(posts_count)
                }

# Удаление аккаунта
@router.post("/settings/delete-account")
async def delete_account(current_user=Depends(get_current_user)):
    if not current_user:
        resp = JSONResponse({"ok": False, "error": "Сессия недействительна"})
        resp.delete_cookie("access_token")
        return resp

    async with session_factory() as session:
        user_Q = await session.execute(
            select(Users).where(Users.username == current_user.username)
        )
        user = user_Q.scalar_one_or_none()

        if not user:
            return JSONResponse({"ok": False, "error": "Не удалось удалить аккаунт"})

        if user.avatar_url and "cloudinary.com" in user.avatar_url:
            await asyncio.to_thread(delete_avatar, user.username)

        await session.delete(user)
        await session.commit()

    response = JSONResponse({"ok": True})
    response.delete_cookie("access_token")
    return response


# == WEBSOCKETS ==

@router.websocket("/chats/{username}/ws")
async def chat_websocket_endpoint(username: str, websocket: WebSocket, current_user=Depends(get_current_user)):
    if not current_user:
        await websocket.close()
        return

    await manager.connect(current_user.id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            text = message_data.get("text", "").strip()
            if not text:
                continue

            async with session_factory() as session:
                companion_Q = await session.execute(
                    select(Users).where(Users.username == username)
                )

                companion = companion_Q.scalar_one_or_none()

                if not companion:
                    continue

                msg = Messages(
                    sender_id=current_user.id,
                    receiver_id=companion.id,
                    text=text
                )
                session.add(msg)
                await session.commit()
                await session.refresh(msg)

                companion_id = companion.id
                time_str = format_time_H_M(msg.created_at)

            await manager.send_to_user(companion_id, {
                "text": text,
                "time": time_str,
                "is_mine": False
            })

    except WebSocketDisconnect:
        manager.disconnect(current_user.id, websocket)

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Просто держим соединение живым
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)