from ninja import Schema, ModelSchema
from datetime import date
from typing import List, Literal
from pydantic import field_validator, constr
from job.models import Job


class SalaryRange(Schema):
    type: Literal['annually', 'monthly']
    currency: str
    min: int
    max: int


class JobCreationRequest(Schema):
    title: constr(min_length=1, max_length=200)
    description: str
    location: constr(max_length=200)
    salary_range: SalaryRange
    company_name: constr(max_length=200)
    posting_date: date
    expiration_date: date
    required_skills: List[constr(max_length=100)]

    @field_validator('posting_date')
    @classmethod
    def validate_posting_date(cls, v):
        today = date.today()
        if v < today:
            raise ValueError('Posting date cannot be earlier than today')
        return v

    @field_validator('expiration_date')
    @classmethod
    def validate_expiration_date(cls, v, info):
        values = info.data
        if 'posting_date' in values and v < values['posting_date']:
            raise ValueError('Expiration date cannot be earlier than posting date')
        return v

    @field_validator('salary_range')
    @classmethod
    def validate_salary_range(cls, v):
        # Ensure minimum salary is less than maximum salary
        if v.min >= v.max:
            raise ValueError('Minimum salary must be less than maximum salary')

        # Ensure salaries are positive numbers
        if v.min <= 0 or v.max <= 0:
            raise ValueError('Salary must be positive numbers')

        # Set reasonable salary limit
        if v.max > 10000000:
            raise ValueError('Salary exceeds reasonable limits')

        return v

    @field_validator('required_skills')
    @classmethod
    def validate_required_skills(cls, v):
        if len(v) == 0:
            return v
        if any(not skill.strip() for skill in v):
            raise ValueError('Skills cannot be empty strings')
        return v


class JobCreationResponse(ModelSchema):
    class Config:
        model = Job
        model_fields = "__all__"


class JobListResponse(Schema):
    data: List[JobCreationResponse]
    current_page: int
    page_size: int
    total_pages: int
    total_count: int
