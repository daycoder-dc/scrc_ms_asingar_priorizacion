from src.config.settings import Settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

settings = Settings()

db_uri = f"postgresql://{settings.database_user}:{settings.database_pass}@{settings.database_host}:{settings.database_port}/{settings.database_name}"
db_engine = "adbc"

__engine__ = create_engine(db_uri)

def get_session():
    with Session(__engine__) as session:
        yield session
