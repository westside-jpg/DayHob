from sqlalchemy import select
from sqlalchemy.sql.expression import insert, delete

from database import session_factory
from models import Users, PendingUsers
from config import settings
import re
import bcrypt
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# == РЕГИСТРАЦИЯ == #
def check_email(email: str):
    with session_factory() as session:
        query = select(Users).where(Users.email == email)
        result = session.execute(query)
        if result.first() is None:
            return True
        else:
            return False

def check_username(username: str):
    with session_factory() as session:
        query = select(Users).where(Users.username == username)
        result = session.execute(query)
        if result.first() is None:
            return True
        else:
            return False

def check_register(username, email, password, confirm_password):
    errors = []

    username = username.strip()
    email = email.strip().lower()

    # проверка username
    if not username:
        errors.append("Имя пользователя не может быть пустым")
    else:
        # проверка длины username
        if len(username) < 3 or len(username) > 50:
            errors.append("Длина имени пользователя должна быть от 3 до 50 символов")
        # проверка на валидность username
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append("Имя пользователя может содержать только латинские буквы, цифры и _")

    # проверка email'а
    if not email:
        errors.append("Поле почты не может быть пустым")
    else:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            errors.append("Неверный формат email'а")
        elif len(email) > 254:
            errors.append("Слишком длинный email")
        elif ".." in email:
            errors.append("Недопустимый формат email'а")

    # проверка пароля
    if not password:
        errors.append("Пароль не может быть пустым")
    else:
        # проверка на длину пароля
        if len(password) < 8 or len(password) > 100:
            errors.append("Длина пароля должна быть от 8 до 100 символов")
        # проверка на сложность пароля
        if not re.search(r'[a-zA-Z]', password):
            errors.append("Пароль должен содержать хотя бы одну букву")
        if not re.search(r'[0-9]', password):
            errors.append("Пароль должен содержать хотя бы одну цифру")

    # проверка на совпадение password и confirm_password
    if password != confirm_password:
        errors.append("Пароли не совпадают")

    if not errors:
        # проверка на уникальность emali'а
        good_email = check_email(email)
        if not good_email:
            errors.append("Такой email уже зарегестрирован")

        # проверка на уникальность username
        good_username = check_username(username)
        if not good_username:
            errors.append("Такое имя пользователя уже занято")

    return (errors if errors else None, username, email)

def hash_password(password: str):
    salt = bcrypt.gensalt(rounds=10)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    hashed_password = hashed_password.decode('utf-8')
    return hashed_password

def register_pending_user(username: str, password: str, email: str) -> str:
    code = str(random.randint(100000, 999999))
    with session_factory() as session:
        session.add(PendingUsers(
            username=username,
            email=email,
            password=password,
            code=code))
        session.commit()
    return code


def send_verification_email(email: str, code: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.MAIL_EMAIL
        msg["To"] = email
        msg["Subject"] = "Подтверждение почты — DayHob"

        body = f"<p>Ваш код подтверждения: <b>{code}</b></p><p>Не передавайте его никому.</p>"
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP("smtp.office365.com", 587, timeout=10) as server:
            server.starttls()
            server.login(settings.MAIL_EMAIL, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_EMAIL, email, msg.as_string())

    except Exception as e:
        print(f"Ошибка отправки письма: {e}")

def check_verification_email_and_register(email: str, input_code: str):
    with session_factory() as session:
        query = select(
            PendingUsers.username,
            PendingUsers.password,
            PendingUsers.email
        ).where(
            PendingUsers.email == email,
            PendingUsers.code == input_code
        )
        result = session.execute(query)

        row = result.first()

        if not row:
            error = "Код введен неверно или пользователь с такой почтой не найден"
            return False, error

        username, password, email = row

        query = insert(Users).values(
            username=username,
            password=password,
            email=email
        )
        session.execute(query)

        query = delete(PendingUsers).where(PendingUsers.email == email)
        session.execute(query)
        session.commit()

    return True, None

# == ВХОД == #
def verify_login(input_username: str, input_password: str):
    with session_factory() as session:
        query = select(Users.password).where(Users.username == input_username)
        result = session.execute(query)
        row = result.first()

        if row is None:
            error = "Пользователь с таким именем не найден"
            return False, error

        password_db = row[0]

        is_valid = bcrypt.checkpw(input_password.encode('utf-8'), password_db.encode('utf-8'))

        if not is_valid:
            error = "Неверный пароль для пользователя"
            return False, error

        return is_valid, None

