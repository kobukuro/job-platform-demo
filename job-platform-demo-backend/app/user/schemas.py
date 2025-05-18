from datetime import datetime
from ninja import Schema
from pydantic import EmailStr, Field
from typing import Optional


class UserRegistrationRequest(Schema):
    email: EmailStr = Field(...)
    password: str = Field(
        ...,
        min_length=1
    )


class UserRegistrationResponse(Schema):
    id: int
    email: str
    company_id: Optional[int] = None
    is_superuser: bool
    created_at: datetime
    last_updated_at: datetime
