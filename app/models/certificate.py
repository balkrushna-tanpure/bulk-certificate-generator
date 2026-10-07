from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_code = Column(String(64), unique=True, nullable=False, index=True)
    
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = Column(String(36), ForeignKey("recipients.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    issuer_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="certificates")
    recipient = relationship("Recipient", back_populates="certificate")
