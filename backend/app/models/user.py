import uuid
from sqlalchemy import Column, String, DateTime, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)       # Argon2id
    encryption_salt = Column(LargeBinary, nullable=False)  # salt para derivar a chave de criptografia
    created_at = Column(DateTime(timezone=True), server_default=func.now())