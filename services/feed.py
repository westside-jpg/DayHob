from datetime import datetime, timezone, timedelta
import zoneinfo

from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import select, delete
from sqlalchemy.sql.functions import func

from database import session_factory
from models import Pushes, created_at


def time_ago(dt):
    diff = datetime.now(timezone.utc) - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "только что"
    elif seconds < 3600:
        mins = int(seconds // 60)
        return f"{mins} мин. назад"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} ч. назад"
    elif seconds < 2592000:
        days = int(seconds // 86400)
        return f"{days} дн. назад"
    elif seconds < 31536000:
        months = int(seconds // 2592000)
        return f"{months} мес. назад"
    else:
        years = int(seconds // 31536000)
        return f"{years} г. назад"

# def time_until_next_day():
#     tz = zoneinfo.ZoneInfo("Asia/Vladivostok")
#     now = datetime.now(tz)
#     tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
#     diff = tomorrow - now
#
#     hours = int(diff.total_seconds() // 3600)
#     minutes = int((diff.total_seconds() % 3600) // 60)
#
#     return f"{hours:02d}:{minutes:02d}"

def cut_numbers(number):
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{number / 1_000:.1f}K"
    return number

def declination_subs(number):
    n = abs(number)
    if 11 <= n % 100 <= 14:
        return "сабов"
    last_digit = n % 10
    if last_digit == 1:
        return "саб"
    elif 2 <= last_digit <= 4:
        return "саба"
    else:
        return "сабов"

def declination_friends(number):
    n = abs(number)
    if 11 <= n % 100 <= 14:
        return "друзей"
    last_digit = n % 10
    if last_digit == 1:
        return "друг"
    elif 2 <= last_digit <= 4:
        return "друга"
    else:
        return "друзей"

def declination_posts(number):
    n = abs(number)
    if 11 <= n % 100 <= 14:
        return "постов"
    last_digit = n % 10
    if last_digit == 1:
        return "пост"
    elif 2 <= last_digit <= 4:
        return "поста"
    else:
        return "постов"

def declination_following(number):
    n = abs(number)
    if 11 <= n % 100 <= 14:
        return "подписок"
    last_digit = n % 10
    if last_digit == 1:
        return "подписка"
    elif 2 <= last_digit <= 4:
        return "подписки"
    else:
        return "подписок"

def declination_pushes(number):
    n = abs(number)
    if 11 <= n % 100 <= 14:
        return "новых уведомлений"
    last_digit = n % 10
    if last_digit == 1:
        return "новое уведомление"
    elif 2 <= last_digit <= 4:
        return "новых уведомления"
    else:
        return "новых уведомлений"

def cut_text(text):
    if not text:
        return ""
    if len(text) > 70:
        return f"{text[:70]}..."
    else:
        return text


def delete_old_pushes(user_id):
    with session_factory() as session:

        count = session.execute(
            select(func.count()).where(Pushes.user_id == user_id)
        ).scalar()

        if count > 250:
            old_ids = session.execute(
                select(Pushes.id)
                .where(Pushes.user_id == user_id)
                .order_by(Pushes.created_at.desc())
                .offset(250)
            ).scalars().all()

            session.execute(
                delete(Pushes).where(Pushes.id.in_(old_ids))
            )
            session.commit()

def cut_pushes_count(pushes_count):
    if pushes_count > 99:
        return "99+"
    return str(pushes_count)

def unread_pushes_count_func(current_user):
    with session_factory() as session:
        count = session.execute(
            select(func.count())
            .select_from(Pushes)
            .where(Pushes.user_id == current_user.id, Pushes.is_read == False)
        ).scalar_one_or_none()

        return count