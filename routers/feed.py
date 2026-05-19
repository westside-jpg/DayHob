from datetime import date
from urllib import request
from fastapi import APIRouter, Request, Form, Depends, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import and_, update
from sqlalchemy.sql.functions import func
from models import Tasks, Posts, Users, Likes, Comments, Followers, Pushes, PushType
from database import session_factory
from services.dependencies import get_current_user
from services.feed import time_ago, declination_friends, declination_subs, declination_posts, \
    cut_numbers, declination_pushes, cut_text, delete_old_pushes, cut_pushes_count, unread_pushes_count_func
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

        unread_pushes_count = unread_pushes_count_func(current_user)

        return templates.TemplateResponse("feed/feed.html", {
            "request": request,
            "task": task,
            "posts": posts,
            "current_user": current_user,
            "unread_pushes_count": cut_pushes_count(unread_pushes_count),
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

    unread_pushes_count = unread_pushes_count_func(current_user)

    return templates.TemplateResponse("feed/search.html", {
        "request": request,
        "current_user": current_user,
        "results": results,
        "unread_pushes_count": cut_pushes_count(unread_pushes_count),
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

        unread_pushes_count = unread_pushes_count_func(current_user)

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
            "unread_pushes_count": cut_pushes_count(unread_pushes_count)
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

    unread_pushes_count = unread_pushes_count_func(current_user)

    return templates.TemplateResponse("feed/settings.html", {
        "request": request,
        "current_user": current_user,
        "unread_pushes_count": cut_pushes_count(unread_pushes_count)
    })

# Друзья
@router.get("/friends")
def get_friends(request: Request, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        f1 = aliased(Followers)
        f2 = aliased(Followers)

        friends_count = session.execute(
            select(func.count())
            .select_from(f1)
            .join(f2, and_(
                f1.following_id == f2.follower_id,
                f2.following_id == current_user.id
            ))
            .where(f1.follower_id == current_user.id)
        ).scalar()

        friends_ids = session.execute(
            select(f1.following_id)
            .join(f2, and_(
                f1.following_id == f2.follower_id,
                f2.following_id == current_user.id
            ))
            .where(f1.follower_id == current_user.id)
        ).scalars().all()

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
            .where(Posts.user_id.in_(friends_ids))
            .order_by(Posts.created_at.desc())
        ).all()

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

        unread_pushes_count = unread_pushes_count_func(current_user)

        return templates.TemplateResponse("feed/friends.html", {
            "request": request,
            "posts": posts,
            "current_user": current_user,
            "friends_count": friends_count,
            "friends_declination": declination_friends(friends_count),
            "unread_pushes_count": cut_pushes_count(unread_pushes_count)
        })

# Пуши
@router.get("/push")
def get_push(request: Request, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        push_count = session.execute(
            select(func.count()).select_from(Pushes)
            .where(Pushes.user_id == current_user.id, Pushes.is_read == False)
        ).scalar()

        unread_pushes = session.execute(
            select(Pushes, Users)
            .outerjoin(Users, Pushes.sender_id == Users.id)
            .where(Pushes.user_id == current_user.id, Pushes.is_read == False)
            .order_by(Pushes.created_at.desc())
        ).all()

        read_pushes = session.execute(
            select(Pushes, Users)
            .outerjoin(Users, Pushes.sender_id == Users.id)
            .where(Pushes.user_id == current_user.id, Pushes.is_read == True)
            .order_by(Pushes.created_at.desc())
        ).all()

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

        session.execute(
            update(Pushes)
            .where(Pushes.user_id == current_user.id, Pushes.is_read == False)
            .values(is_read=True)
        )

        session.commit()

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
def get_friends_list(request: Request, username: str, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        user = session.execute(
            select(Users).where(Users.username == username)
        ).scalar_one_or_none()

        f1 = aliased(Followers)
        f2 = aliased(Followers)

        friends_count = session.execute(
            select(func.count())
            .select_from(f1)
            .join(f2, and_(
                f1.following_id == f2.follower_id,
                f2.following_id == current_user.id
            ))
            .where(f1.follower_id == current_user.id)
        ).scalar()

        friends_ids = session.execute(
            select(f1.following_id)
            .join(f2, and_(
                f1.following_id == f2.follower_id,
                f2.following_id == user.id
            ))
            .where(f1.follower_id == user.id)
        ).scalars().all()

        rows = session.execute(
            select(Users)
            .where(Users.id.in_(friends_ids))
        ).scalars().all()

        results = []

        for result in rows:
            results.append({
                "username": result.username,
                "avatar_url": result.avatar_url,
            })

        unread_pushes_count = unread_pushes_count_func(current_user)

        return templates.TemplateResponse("feed/subs_and_friends_list.html", {
            "request": request,
            "current_user": current_user,
            "count": friends_count,
            "declination": declination_friends(friends_count),
            "results": results,
            "unread_pushes_count": cut_pushes_count(unread_pushes_count)
        })


# Список подписчиков пользователя
@router.get("/profile/{username}/subs_list")
def get_subs_list(request: Request, username: str, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        user = session.execute(
            select(Users).where(Users.username == username)
        ).scalar_one_or_none()

        subs_count = session.execute(
            select(func.count())
            .select_from(Followers)
            .where(Followers.following_id == user.id)
        ).scalar()

        subs_ids = session.execute(
            select(Followers.follower_id)
            .where(Followers.following_id == user.id)
        ).scalars().all()

        rows = session.execute(
            select(Users)
            .where(Users.id.in_(subs_ids))
        ).scalars().all()

        results = []

        for result in rows:
            results.append({
                "username": result.username,
                "avatar_url": result.avatar_url,
            })

        unread_pushes_count = unread_pushes_count_func(current_user)

        return templates.TemplateResponse("feed/subs_and_friends_list.html", {
            "request": request,
            "current_user": current_user,
            "count": subs_count,
            "declination": declination_subs(subs_count),
            "results": results,
            "unread_pushes_count": cut_pushes_count(unread_pushes_count)
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

        post = session.execute(
            select(Posts)
            .where(Posts.id == post_id)
        ).scalar_one_or_none()

        if existing:
            session.delete(existing)

            if post.user_id != current_user.id:
                push = session.execute(
                    select(Pushes)
                    .where(
                        Pushes.post_id == post_id,
                        Pushes.type == PushType.LIKE,
                        Pushes.user_id == post.user_id,
                        Pushes.sender_id == current_user.id
                    )
                ).scalar_one_or_none()

                if push:
                    session.delete(push)

            session.commit()
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
                delete_old_pushes(post.user_id)
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

        # Проверяем подписан ли user на current_user
        reverse = session.execute(
            select(Followers).where(
                Followers.following_id == current_user.id,
                Followers.follower_id == user.id
            )
        ).scalar_one_or_none()

        if existing:
            session.delete(existing)

            push_sub = session.execute(
                select(Pushes)
                .where(
                    Pushes.user_id == user.id,
                    Pushes.sender_id == current_user.id,
                    Pushes.type == PushType.FOLLOW,
                )
            ).scalar_one_or_none()

            if push_sub:
                session.delete(push_sub)

            if reverse:
                push_fri_1 = session.execute(
                    select(Pushes)
                    .where(
                        Pushes.user_id == user.id,
                        Pushes.sender_id == current_user.id,
                        Pushes.type == PushType.FRIENDS,
                    )
                ).scalar_one_or_none()

                push_fri_2 = session.execute(
                    select(Pushes)
                    .where(
                        Pushes.user_id == current_user.id,
                        Pushes.sender_id == user.id,
                        Pushes.type == PushType.FRIENDS,
                    )
                ).scalar_one_or_none()

                if push_fri_1:
                    session.delete(push_fri_1)

                if push_fri_2:
                    session.delete(push_fri_2)

            session.commit()
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
            delete_old_pushes(user.id)

            if reverse:
                session.add(Pushes(
                    user_id=user.id,
                    sender_id=current_user.id,
                    text=f"Теперь Ваш друг",
                    is_read=False,
                    type=PushType.FRIENDS,
                ))
                delete_old_pushes(user.id)

                session.add(Pushes(
                    user_id=current_user.id,
                    sender_id=user.id,
                    text=f"Теперь Ваш друг",
                    is_read=False,
                    type=PushType.FRIENDS,
                ))
                delete_old_pushes(current_user.id)

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

        unread_pushes_count = unread_pushes_count_func(current_user)

        return {"is_subscribed": is_subscribed,
                "followers_count": cut_numbers(followers_count),
                "declination_subs": declination_subs(followers_count),
                "friends_count": cut_numbers(friends_count),
                "declination_friends": declination_friends(friends_count),
                "unread_pushes_count": cut_pushes_count(unread_pushes_count)
                }

# Логика публикации коммента
@router.post("/post/{post_id}/post-comment")
def post_comment(post_id: int, text: str = Form(...), current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    if len(text) > 500:
        return {"error": "Длина комментария больше 500 символов"}

    with session_factory() as session:
        session.add(Comments(
            post_id=post_id,
            user_id=current_user.id,
            text=text
        ))

        post = session.execute(
            select(Posts)
            .where(Posts.id == post_id)
        ).scalar_one_or_none()

        if not post:
            return {"error": "not found"}

        if post.user_id != current_user.id:
            session.add(Pushes(
                user_id=post.user_id,
                sender_id=current_user.id,
                post_id = post_id,
                text=f"Написал комментарий к вашему посту \"{cut_text(post.text)}\": \"{cut_text(text)}\"",
                is_read=False,
                type=PushType.COMMENT,
            ))
            delete_old_pushes(post.user_id)
        session.commit()

    return {"ok": True}

# Ручка обновления настроек
@router.post("/settings/apply")
def update_settings(
    bio: str = Form(None),
    avatar: UploadFile = File(None),
    current_user=Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    if bio is not None and len(bio) > 150:
        return {"error": "Максимальная длина описания профиля — 150 символов"}

    with session_factory() as session:
        user = session.execute(
            select(Users).where(Users.username == current_user.username)
        ).scalar_one_or_none()

        user.bio = bio

        if avatar and avatar.filename:
            user.avatar_url = upload_avatar(avatar.file, current_user.username)

        session.commit()
        return {"avatar_url": user.avatar_url, "bio": user.bio}

# Ручка удаления поста
@router.post("/post/{post_id}/delete")
def delete_post(post_id: int, current_user=Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    with session_factory() as session:
        post = session.execute(
            select(Posts)
            .where(Posts.id == post_id)
        ).scalar_one_or_none()

        if not post:
            return {"error": "Ошибка удаления"}

        if post.user_id != current_user.id:
            return {"error": "У Вас нет прав удалить этот пост"}

        session.delete(post)
        session.commit()

        posts_count =  session.execute(
            select(func.count()).select_from(Posts)
            .where(Posts.user_id == current_user.id)
        ).scalar()

        return {"ok": True,
                "message": "Ваш пост был успешно удален",
                "count": posts_count,
                "declination": declination_posts(posts_count)
                }
