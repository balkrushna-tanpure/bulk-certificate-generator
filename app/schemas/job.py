from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.models.job import JobStatus
from app.schemas.recipient import RecipientInput, RecipientResponse

class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Event or Course title")
    description: Optional[str] = Field(None, description="Optional description on the certificate")
    issuer_name: str = Field(..., min_length=1, max_length=255, description="Organization or Issuer name")
    issue_date: Optional[str] = Field(None, max_length=50, description="Date formatted string, e.g. 'October 7, 2026' or '2026-10-07'")
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipient records to generate certificates for")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Job title cannot be empty.")
        return stripped

    @field_validator("issuer_name")
    @classmethod
    def validate_issuer_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Issuer name cannot be empty.")
        return stripped

    @field_validator("recipients")
    @classmethod
    def validate_recipients_not_empty(cls, v: List[RecipientInput]) -> List[RecipientInput]:
        if not v or len(v) == 0:
            raise ValueError("Recipients list cannot be empty. At least one recipient is required.")
        return v

class JobResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    issuer_name: str
    issue_date: str
    status: JobStatus
    total_recipients: int
    processed_count: int
    success_count: int
    failure_count: int
    progress_percentage: float = 0.0
    error_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    status_url: Optional[str] = None
    download_all_url: Optional[str] = None

    model_config = {"from_attributes": True}

class JobDetailResponse(JobResponse):
    recipients: List[RecipientResponse] = []
