from datetime import datetime, timezone, timedelta
import zoneinfo

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