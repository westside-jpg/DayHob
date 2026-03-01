from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL_psycopg: str
    MAIL_EMAIL: str
    MAIL_PASSWORD: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()