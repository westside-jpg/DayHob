from fastapi import Cookie
from sqlalchemy import select
from database import session_factory
from models import Users
from services.auth_jwt import decode_access_token


def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        return None

    username = decode_access_token(access_token)
    if not username:
        return None

    with session_factory() as session:
        query = select(Users).where(Users.username == username)
        result = session.execute(query)
        user = result.scalar_one_or_none()
        return user