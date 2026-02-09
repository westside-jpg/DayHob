from datetime import datetime, date
from sqlalchemy import String, text, ForeignKey, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from typing import Annotated

created_at = Annotated[datetime, mapped_column(DateTime(timezone=True), server_default=func.now())]

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[created_at]

class Tasks(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2000))

class Posts(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    text: Mapped[str] = mapped_column(String(1024))
    image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[created_at]
