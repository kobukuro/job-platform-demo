from datetime import datetime
from ninja import Schema
from pydantic import EmailStr, Field, field_validator
import re
from typing import Optional


def validate_password_complexity(password: str) -> str:
    """
    Validate password complexity:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one number")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("Password must contain at least one special character")

    return password


class UserRegistrationRequest(Schema):
    email: EmailStr = Field(...)
    password: str = Field(
        ...,
        min_length=8,
        description="Password must contain at least 8 characters, including uppercase, lowercase, number and special character"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_complexity(v)


class UserRegistrationResponse(Schema):
    id: int
    email: str
    company_id: Optional[int] = None
    is_superuser: bool
    created_at: datetime
    last_updated_at: datetime


class UserLoginRequest(Schema):
    email: EmailStr = Field(...)
    password: str = Field(
        ...,
        min_length=8,
        description="Password must contain at least 8 characters, including uppercase, lowercase, number and special character"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_complexity(v)


class UserLoginResponse(Schema):
    access_token: str
    refresh_token: str


class TokenRefreshRequest(Schema):
    refresh_token: str


class TokenRefreshResponse(Schema):
    access_token: str
