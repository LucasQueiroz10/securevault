from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# check_same_thread=False é necessário só para SQLite: por padrão ele bloqueia
# uso da mesma conexão em threads diferentes, mas o FastAPI pode servir
# requisições em threads diferentes. Não se aplica a PostgreSQL (será removido
# quando migrarmos).
engine = create_engine(
    settings.database_url.get_secret_value(),
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()