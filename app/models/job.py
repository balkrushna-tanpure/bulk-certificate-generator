import enum
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from app.database import Base

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    FAILED = "FAILED"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    issuer_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    total_recipients = Column(Integer, default=0, nullable=False)
    processed_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    
    error_summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships ordered deterministically
    recipients = relationship("Recipient", back_populates="job", cascade="all, delete-orphan", order_by="Recipient.sequence_index")
    certificates = relationship("Certificate", back_populates="job", cascade="all, delete-orphan", order_by="Certificate.created_at")
