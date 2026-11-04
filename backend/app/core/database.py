from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

database_url = settings.database_url.get_secret_value()

# check_same_thread=False é necessário só para SQLite: por padrão ele bloqueia
# uso da mesma conexão em threads diferentes, mas o FastAPI pode servir
# requisições em threads diferentes. O driver do PostgreSQL recusa essa opção.
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()