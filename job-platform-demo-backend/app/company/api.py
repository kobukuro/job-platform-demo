from django.http.request import HttpRequest
from django.db import transaction, IntegrityError
from ninja import Router
from ninja.responses import Response
from ninja.errors import HttpError
from company.models import Company
from company.schemas import CompanyCreationRequest, CompanyCreationResponse

router = Router(tags=['Company'])


@router.post("", response={201: CompanyCreationResponse})
def create_company(request: HttpRequest, payload: CompanyCreationRequest) -> Response:
    """
    Create a new company with atomicity guarantee.

    Args:
        request: The HTTP request object
        payload: Validated company creation data

    Returns:
        Response with status code 201 on success

    Raises:
        HttpError:
            - 400 for client-side errors
            - 500 for server-side errors
    """
    try:
        with transaction.atomic():
            company = Company.objects.create(
                name=payload.name
            )
        return Response(CompanyCreationResponse.from_orm(company).dict(), status=201)

    except IntegrityError as e:
        raise HttpError(409, "Company with this name already exists")
    except Exception as e:
        raise HttpError(500, "Internal server error")

@router.delete("/{company_id}", response={204: None})
def delete_company(request: HttpRequest, company_id: int) -> Response:
    """
    Delete an existing company by ID.

    Args:
        request: The HTTP request object
        company_id: The ID of the company to delete

    Returns:
        Response with status code 204 on success

    Raises:
        HttpError:
            - 404 if company not found
            - 500 for server-side errors
    """
    try:
        with transaction.atomic():
            company = Company.objects.get(id=company_id)
            company.delete()
        return Response(None, status=204)

    except Company.DoesNotExist:
        raise HttpError(404, "Company not found")
    except Exception as e:
        raise HttpError(500, "Internal server error")

