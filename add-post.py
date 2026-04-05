from database import session_factory
from models import Posts, Tasks, Users
from sqlalchemy import select
from datetime import date

with session_factory() as session:
    # Берём существующего пользователя
    user = session.execute(select(Users).where(Users.username == "danya")).scalar_one()

    # Берём существующее задание
    task = session.execute(select(Tasks).where(Tasks.date == date.today())).scalar_one()

    # Добавляем новый пост
    post = Posts(
        user_id=user.id,
        task_id=task.id,
        text="",
        image_url=""
    )
    session.add(post)
    session.commit()

print("Пост добавлен!")