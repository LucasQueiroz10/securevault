import uuid
import enum
from sqlalchemy import Column, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class AuditAction(str, enum.Enum):
    CREATED = "created"
    VIEWED = "viewed"
    UPDATED = "updated"
    DELETED = "deleted"
    PASSWORD_COPIED = "password_copied"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    credential_id = Column(UUID(as_uuid=True), ForeignKey("credentials.id"), nullable=True)
    action = Column(Enum(AuditAction), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())