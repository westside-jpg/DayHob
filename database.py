from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

sync_engine = create_engine(
    url=settings.DATABASE_URL_psycopg,
    echo=True,
    pool_size=5,
    max_overflow=10,
)

session_factory = sessionmaker(sync_engine)