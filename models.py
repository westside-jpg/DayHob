from datetime import datetime, date
from sqlalchemy import String, ForeignKey, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from typing import Annotated

from sqlalchemy.sql.schema import UniqueConstraint

created_at = Annotated[datetime, mapped_column(DateTime(timezone=True), server_default=func.now())]

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[created_at]

class PendingUsers(Base):
    __tablename__ = "pending_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(6))
    created_at: Mapped[created_at]

class Tasks(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

class Posts(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    text: Mapped[str] = mapped_column(String(1024))
    image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[created_at]

class Likes(Base):
    __tablename__ = "likes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)
    liked_at: Mapped[created_at]

class Comments(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)
    text: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[created_at]

class Followers(Base):
    __tablename__ = "followers"
    id: Mapped[int] = mapped_column(primary_key=True)
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    following_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    followed_at: Mapped[created_at]

    __table_args__ = (UniqueConstraint("follower_id", "following_id"),)