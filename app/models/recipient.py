import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class RecipientStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_index = Column(Integer, default=0, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role_or_achievement = Column(String(255), nullable=True)
    
    status = Column(Enum(RecipientStatus), default=RecipientStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    job = relationship("Job", back_populates="recipients")
    certificate = relationship("Certificate", back_populates="recipient", uselist=False, cascade="all, delete-orphan")
