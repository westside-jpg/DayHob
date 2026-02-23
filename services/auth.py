from sqlalchemy import select
from database import session_factory
from models import Users, PendingUsers
import re
import bcrypt
import random

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

def register_pending_user(username, password, email) -> str:
    code = str(random.randint(100000, 999999))
    with session_factory() as session:
        session.add(PendingUsers(
            username=username,
            email=email,
            password=password,
            code=code))
        session.commit()
    return code

def register_user(username, email, password):
    with session_factory() as session:
        session.add(Users(username=username, email=email, password=password))
        session.commit()

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

