from django.db.models.query_utils import Q
from django.http.request import HttpRequest
from django.db import transaction, IntegrityError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ninja import Router, Query
from ninja.responses import Response
from ninja.errors import HttpError
from datetime import date
from typing import List, Optional

from job.schemas import JobCreationRequest, JobCreationResponse, JobListResponse
from job.models import Job
from core.throttling.redis import RedisThrottle
from core.authz.jwt_auth import CustomJWTAuth, OptionalJWTAuth, AnonymousUser
from job_platform_demo_backend.exceptions import JobUpdateError

router = Router(tags=['Job'])


@router.post("", response={201: JobCreationResponse}, throttle=[RedisThrottle("10/second")],
             auth=CustomJWTAuth())
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
            user = request.auth
            if not user.is_superuser:
                if user.company is None or user.company.name != payload.company_name:
                    raise HttpError(403, "You don't have permission to create jobs for this company")

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
                status=status,
                created_by=user,
                last_updated_by=user
            )
            job.save()

        return Response(JobCreationResponse.from_orm(job).dict(), status=201)

    except HttpError:
        raise

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


@router.get("", response=JobListResponse, throttle=[RedisThrottle("20/second")],
            auth=OptionalJWTAuth())
def list_jobs(
        request: HttpRequest,
        title: Optional[str] = None,
        description: Optional[str] = None,
        company_name: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
        required_skills: Optional[List[str]] = Query(None),
        salary_type: Optional[str] = None,
        salary_currency: Optional[str] = None,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        posting_date_start: Optional[date] = None,
        posting_date_end: Optional[date] = None,
        expiration_date_start: Optional[date] = None,
        expiration_date_end: Optional[date] = None,
        order_by: Optional[str] = None,  # 'posting_date' or 'expiration_date'
        order_direction: Optional[str] = 'asc',  # 'asc' or 'desc'
        page: int = 1,
        page_size: int = 10
) -> Response:
    """
    Retrieve a list of job postings with comprehensive search, filter and sorting options.

    Authorization:
    - Unauthenticated users can only view jobs with 'active' status
    - Authenticated users can view 'active' jobs and their own created jobs
    - Superusers can view all jobs regardless of status

    Args:
        request: The HTTP request object
        title: Filter by job title (partial match)
        description: Filter by job description (partial match)
        company_name: Filter by company name (partial match)
        location: Filter by job location (partial match)
        status: Filter by job status (active/expired/scheduled)
        required_skills: Filter by required skills
        salary_type: Filter by salary type (annually/monthly)
        salary_currency: Filter by salary currency
        min_salary: Filter by minimum salary
        max_salary: Filter by maximum salary
        posting_date_start: Filter by posting date (start range)
        posting_date_end: Filter by posting date (end range)
        expiration_date_start: Filter by expiration date (start range)
        expiration_date_end: Filter by expiration date (end range)
        order_by: Field to sort by (posting_date/expiration_date)
        order_direction: Sort direction (asc/desc)
        page: Page number for pagination
        page_size: Number of items per page

    Returns:
        JobListResponse containing paginated job listings and metadata
    """
    queryset = Job.objects.all()

    user = request.auth
    if type(user) is AnonymousUser:
        # Unauthenticated users can only see active jobs
        queryset = queryset.filter(status='active')
    else:
        if not user.is_superuser:
            # Normal authenticated users can see their own jobs and active jobs
            queryset = queryset.filter(
                Q(status='active') |
                Q(created_by=user)
            )

    # Search filters
    if title:
        queryset = queryset.filter(title__icontains=title)
    if description:
        queryset = queryset.filter(description__icontains=description)
    if company_name:
        queryset = queryset.filter(company_name__icontains=company_name)
    if location:
        queryset = queryset.filter(location=location)
    if status:
        queryset = queryset.filter(status=status)
    if required_skills:
        for skill in required_skills:
            queryset = queryset.filter(required_skills__contains=[skill])

    # Salary range filters
    if any([min_salary, max_salary]):
        if not salary_type or not salary_currency:
            raise HttpError(
                400,
                "Salary type and currency are required for salary range filtering"
            )
        salary_filter = {
            'salary_range__type': salary_type,
            'salary_range__currency': salary_currency
        }

        if min_salary is not None:
            salary_filter['salary_range__max__gte'] = min_salary

        if max_salary is not None:
            salary_filter['salary_range__min__lte'] = max_salary

        queryset = queryset.filter(**salary_filter)

    # Date range filters
    if posting_date_start:
        queryset = queryset.filter(posting_date__gte=posting_date_start)
    if posting_date_end:
        queryset = queryset.filter(posting_date__lte=posting_date_end)
    if expiration_date_start:
        queryset = queryset.filter(expiration_date__gte=expiration_date_start)
    if expiration_date_end:
        queryset = queryset.filter(expiration_date__lte=expiration_date_end)

    # Ordering
    if order_by:
        order_field = order_by
        if order_direction == 'desc':
            order_field = f'-{order_field}'
        queryset = queryset.order_by(order_field)

    paginator = Paginator(queryset, page_size)

    try:
        paginated_jobs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        paginated_jobs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        paginated_jobs = paginator.page(paginator.num_pages)

    return JobListResponse(
        data=[JobCreationResponse.from_orm(job) for job in paginated_jobs],
        current_page=page,
        page_size=page_size,
        total_pages=paginator.num_pages,
        total_count=paginator.count
    )


@router.get("/{job_id}", response=JobCreationResponse, throttle=[RedisThrottle("20/second")],
            auth=OptionalJWTAuth())
def get_job(request: HttpRequest, job_id: int) -> Response:
    """
    Retrieve a single job posting by its ID.

    Authorization:
    - Unauthenticated users can only view jobs with 'active' status
    - Authenticated users can view 'active' jobs and their own created jobs
    - Superusers can view all jobs regardless of status

    Args:
        request: The HTTP request object
        job_id: The unique identifier of the job posting

    Returns:
        JobCreationResponse containing the job posting details

    Raises:
        HttpError:
            - 404 if job posting is not found or user doesn't have permission to view it
            - 500 for server-side errors
    """
    try:
        job = Job.objects.get(id=job_id)
        # Permission check
        user = request.auth
        if type(user) is AnonymousUser:
            # Unauthenticated users can only view active jobs
            if job.status != 'active':
                raise HttpError(404, f"Job posting with ID {job_id} not found")
        else:
            if not user.is_superuser:
                # Regular authenticated users can view active jobs and their own jobs
                if job.status != 'active' and job.created_by != user:
                    raise HttpError(404, f"Job posting with ID {job_id} not found")
        return Response(JobCreationResponse.from_orm(job).dict())

    except HttpError:
        raise

    except Job.DoesNotExist:
        raise HttpError(404, f"Job posting with ID {job_id} not found")

    except Exception as e:
        # Handle unexpected errors
        # In production, you should log the error but not expose its details
        raise HttpError(500, "Internal server error")


@router.put("/{job_id}", response=JobCreationResponse, throttle=[RedisThrottle("10/second")],
            auth=CustomJWTAuth())
def update_job(request: HttpRequest, job_id: int, payload: JobCreationRequest) -> Response:
    """
    Update an existing job posting with atomicity guarantee.
    Company name cannot be changed.

    Args:
        request: The HTTP request object
        job_id: The unique identifier of the job posting
        payload: Validated job update data

    Returns:
        JobCreationResponse containing the updated job posting details

    Raises:
        HttpError:
            - 400 for client-side errors (invalid data or validation errors)
            - 404 if job posting is not found
            - 500 for server-side errors
    """
    try:
        with transaction.atomic():
            user = request.auth
            job = Job.objects.get(id=job_id)
            if not user.is_superuser:
                if job.created_by != user:
                    raise HttpError(403, "You don't have permission to update this job")
            # Prevent company name changes
            if payload.company_name != job.company_name:
                raise JobUpdateError("Company name cannot be changed")

            today = date.today()
            status = 'scheduled' if payload.posting_date > today else 'active'

            # Update job fields
            job.title = payload.title
            job.description = payload.description
            job.location = payload.location
            job.salary_range = payload.salary_range.dict()
            job.posting_date = payload.posting_date
            job.expiration_date = payload.expiration_date
            job.required_skills = payload.required_skills
            job.status = status
            job.last_updated_by = user

            job.save()

        return Response(JobCreationResponse.from_orm(job).dict())

    except HttpError:
        raise

    except Job.DoesNotExist:
        raise HttpError(404, f"Job posting with ID {job_id} not found")

    except IntegrityError as e:
        raise HttpError(400, f"Invalid data: {str(e)}")

    except ValueError as e:
        raise HttpError(400, f"Invalid input: {str(e)}")

    except JobUpdateError as e:
        raise HttpError(400, str(e))

    except Exception as e:
        raise HttpError(500, "Internal server error")


@router.delete("/{job_id}", response={204: None}, throttle=[RedisThrottle("5/second")],
               auth=CustomJWTAuth())
def delete_job(request: HttpRequest, job_id: int):
    """
    Delete a job posting by its ID with atomicity guarantee.

    Args:
        request: The HTTP request object
        job_id: The unique identifier of the job posting

    Returns:
        Response with status code 204 on successful deletion

    Raises:
        HttpError:
            - 404 if job posting is not found
            - 500 for server-side errors
    """
    try:
        with transaction.atomic():
            user = request.auth
            job = Job.objects.get(id=job_id)
            if not user.is_superuser:
                if job.created_by != user:
                    raise HttpError(403, "You don't have permission to delete this job")
            job.delete()
            return 204, None
    except HttpError:
        raise

    except Job.DoesNotExist:
        raise HttpError(404, f"Job posting with ID {job_id} not found")

    except Exception as e:
        # Handle unexpected errors
        raise HttpError(500, str(e))
