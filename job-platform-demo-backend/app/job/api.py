from django.http.request import HttpRequest
from django.db import transaction, IntegrityError
from ninja import Router
from ninja.responses import Response
from ninja.errors import HttpError
from datetime import date

from job.schemas import JobCreationRequest, JobCreationResponse
from job.models import Job
from core.throttling.redis import RedisThrottle

router = Router()


@router.post("", response={201: JobCreationResponse}, throttle=[RedisThrottle("10/second")])
def create_job(request: HttpRequest, payload: JobCreationRequest) -> Response:
    """
    Create a new job listing with atomicity guarantee.

    This function wraps the job creation in a database transaction to ensure
    atomicity - either all database operations succeed or none of them do.

    Args:
        request: The HTTP request object
        payload: Validated job creation data

    Returns:
        Response with status code 201 on success

    Raises:
        HttpError:
            - 400 for client-side errors (invalid data or validation errors)
            - 500 for server-side errors
    """
    try:
        with transaction.atomic():
            today = date.today()
            status = 'scheduled' if payload.posting_date > today else 'active'

            job = Job(
                title=payload.title,
                description=payload.description,
                location=payload.location,
                salary_range=payload.salary_range.dict(),
                company_name=payload.company_name,
                posting_date=payload.posting_date,
                expiration_date=payload.expiration_date,
                required_skills=payload.required_skills,
                status=status
            )
            job.save()

        return Response(JobCreationResponse.from_orm(job).dict(), status=201)

    except IntegrityError as e:
        # Handle database integrity errors (e.g., unique constraint violations)
        raise HttpError(400, f"Invalid data: {str(e)}")

    except ValueError as e:
        # Handle validation errors
        raise HttpError(400, f"Invalid input: {str(e)}")

    except Exception as e:
        # Handle unexpected errors
        # In production, you should log the error but not expose its details
        raise HttpError(500, "Internal server error")
