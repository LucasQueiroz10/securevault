from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./securevault.db"

# check_same_thread=False é necessário só para SQLite: por padrão ele bloqueia
# uso da mesma conexão em threads diferentes, mas o FastAPI pode servir
# requisições em threads diferentes. Não se aplica a PostgreSQL (será removido
# quando migrarmos).
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()