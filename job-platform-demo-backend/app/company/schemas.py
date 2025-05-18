from ninja import Schema, ModelSchema
from pydantic import constr
from company.models import Company, CompanyDomain


class CompanyCreationRequest(Schema):
    name: constr(min_length=1, max_length=200)


class CompanyCreationResponse(ModelSchema):
    class Config:
        model = Company
        model_fields = "__all__"


class CompanyDomainCreationRequest(Schema):
    name: constr(min_length=1, max_length=200)


class CompanyDomainCreationResponse(ModelSchema):
    class Config:
        model = CompanyDomain
        model_fields = "__all__"
