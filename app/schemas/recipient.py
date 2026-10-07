import re
from typing import Optional
from pydantic import BaseModel, Field
from app.models.recipient import RecipientStatus

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+(\.[a-zA-Z0-9\-]+)+$")

def is_valid_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def is_valid_name(name: str) -> bool:
    if not name or not isinstance(name, str):
        return False
    return bool(name.strip())

class RecipientInput(BaseModel):
    name: str = Field(..., description="Full name of recipient")
    email: str = Field(..., description="Email address of recipient")
    role_or_achievement: Optional[str] = Field(None, description="Optional role, title or achievement (e.g. 'With Distinction', 'Participant')")

class RecipientResponse(BaseModel):
    id: str
    job_id: str
    name: str
    email: str
    role_or_achievement: Optional[str] = None
    status: RecipientStatus
    error_message: Optional[str] = None
    certificate_id: Optional[str] = None

    model_config = {"from_attributes": True}
