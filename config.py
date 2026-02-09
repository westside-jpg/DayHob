from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # URL для синхронного движка (psycopg3)
    DATABASE_URL_psycopg: str

    class Config:
        env_file = ".env"

settings = Settings()