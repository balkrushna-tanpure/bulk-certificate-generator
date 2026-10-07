from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CertificateResponse(BaseModel):
    id: str
    certificate_code: str
    job_id: str
    recipient_id: str
    recipient_name: str
    recipient_email: str
    title: str
    description: Optional[str] = None
    issuer_name: str
    issue_date: str
    file_size_bytes: int
    download_url: str
    created_at: datetime

    model_config = {"from_attributes": True}

class CertificateVerificationResponse(BaseModel):
    certificate_code: str
    is_valid: bool
    recipient_name: str
    title: str
    issuer_name: str
    issue_date: str
    download_url: str
