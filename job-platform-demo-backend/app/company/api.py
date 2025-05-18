from django.http.request import HttpRequest
from django.db import transaction, IntegrityError
from ninja import Router
from ninja.responses import Response
from ninja.errors import HttpError
from company.models import Company, CompanyDomain
from company.schemas import CompanyCreationRequest, CompanyCreationResponse, CompanyDomainCreationRequest, \
    CompanyDomainCreationResponse

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


@router.post("/{company_id}/domains", response={201: CompanyDomainCreationRequest})
def create_company_domain(request: HttpRequest, company_id: int, payload: CompanyDomainCreationRequest) -> Response:
    """
    Create a new domain for a specific company.

    Args:
        request: The HTTP request object
        company_id: The ID of the company to add the domain to
        payload: Validated domain creation data

    Returns:
        Response with status code 201 on success

    Raises:
        HttpError:
            - 404 if company not found
            - 409 if domain name already exists
            - 500 for server-side errors
    """
    try:
        with transaction.atomic():
            company = Company.objects.get(id=company_id)
            domain = CompanyDomain.objects.create(
                name=payload.name,
                company=company
            )
        return Response(CompanyDomainCreationResponse.from_orm(domain).dict(), status=201)

    except Company.DoesNotExist:
        raise HttpError(404, "Company not found")
    except IntegrityError:
        raise HttpError(409, "Domain with this name already exists")
    except Exception:
        raise HttpError(500, "Internal server error")


@router.delete("/{company_id}/domains/{domain_id}", response={204: None})
def delete_company_domain(request: HttpRequest, company_id: int, domain_id: int) -> Response:
    """
    Delete a domain from a specific company.

    Args:
        request: The HTTP request object
        company_id: The ID of the company
        domain_id: The ID of the domain to delete

    Returns:
        Response with status code 204 on success

    Raises:
        HttpError:
            - 404 if company not found
            - 404 if domain not found
            - 500 for server-side errors
    """
    try:
        with transaction.atomic():
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                raise HttpError(404, "Company not found")

            try:
                domain = CompanyDomain.objects.get(id=domain_id, company=company)
            except CompanyDomain.DoesNotExist:
                raise HttpError(404, "Domain not found")

            domain.delete()
        return Response(None, status=204)

    except HttpError:
        raise
    except Exception:
        raise HttpError(500, "Internal server error")
