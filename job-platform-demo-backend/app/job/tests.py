import pytest
from datetime import date, timedelta
import json
from django.contrib.auth import get_user_model
from job.models import Job
from company.models import Company, CompanyDomain

User = get_user_model()
JOBS_ENDPOINT = "/jobs"
LOGIN_ENDPOINT = "/users/login"


@pytest.fixture
def superuser_credentials():
    return {
        "email": "admin@test.com",
        "password": "password123"
    }


@pytest.fixture
def normal_user_test_company_credentials():
    return {
        "email": "user@test.com",
        "password": "password123"
    }


@pytest.fixture
def normal_user_no_company_credentials():
    return {
        "email": "user@gmail.com",
        "password": "password123"
    }


@pytest.fixture
def superuser(superuser_credentials):
    return User.objects.create_superuser(
        email=superuser_credentials["email"],
        password=superuser_credentials["password"]
    )


@pytest.fixture
def test_company():
    test_company = Company.objects.create(name="Test Corp")
    CompanyDomain.objects.create(name="test.com", company=test_company)


@pytest.fixture
def normal_user_test_company(test_company, normal_user_test_company_credentials):
    return User.objects.create_user(
        email=normal_user_test_company_credentials["email"],
        password=normal_user_test_company_credentials["password"]
    )


@pytest.fixture
def normal_user_no_company(normal_user_no_company_credentials):
    return User.objects.create_user(
        email=normal_user_no_company_credentials["email"],
        password=normal_user_no_company_credentials["password"]
    )


@pytest.fixture
def superuser_token(client, superuser, superuser_credentials):
    response = client.post(
        LOGIN_ENDPOINT,
        data=json.dumps(superuser_credentials),
        content_type="application/json"
    )
    return response.json()["access_token"]


@pytest.fixture
def normal_user_test_company_token(client, normal_user_test_company, normal_user_test_company_credentials):
    response = client.post(
        LOGIN_ENDPOINT,
        data=json.dumps(normal_user_test_company_credentials),
        content_type="application/json"
    )
    return response.json()["access_token"]


@pytest.fixture
def normal_user_no_company_token(client, normal_user_no_company, normal_user_no_company_credentials):
    response = client.post(
        LOGIN_ENDPOINT,
        data=json.dumps(normal_user_no_company_credentials),
        content_type="application/json"
    )
    return response.json()["access_token"]


@pytest.mark.django_db
class TestJobCreationAPI:
    def test_create_job_success_scheduled_test_company_user(self, client, normal_user_test_company_token):
        """Test successful job creation with scheduled posting"""
        tomorrow = date.today() + timedelta(days=1)
        next_month = date.today() + timedelta(days=30)

        payload = {
            "title": "Backend Engineer",
            "description": "Python developer position",
            "location": "Taipei, Taiwan",
            "salary_range": {"type": "annually", "currency": "TWD", "min": "1200000", "max": "1500000"},
            "company_name": "Test Corp",
            "posting_date": tomorrow.isoformat(),
            "expiration_date": next_month.isoformat(),
            "required_skills": ["Python", "Django", "REST API"]
        }

        response = client.post(
            JOBS_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_test_company_token}"
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["status"] == "scheduled"

    def test_create_job_forbidden_no_company_user(self, client, normal_user_no_company_token):
        """Test job creation forbidden for user without company"""
        payload = {
            "title": "Frontend Developer",
            "description": "React developer position",
            "location": "Taipei, Taiwan",
            "salary_range": {"type": "annually", "currency": "TWD", "min": "1200000", "max": "1500000"},
            "company_name": "Test Corp",
            "posting_date": date.today().isoformat(),
            "expiration_date": (date.today() + timedelta(days=30)).isoformat(),
            "required_skills": ["React", "JavaScript", "TypeScript"]
        }

        response = client.post(
            JOBS_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_no_company_token}"
        )
        assert response.status_code == 403

    def test_create_job_immediate_posting_test_company_user(self, client, normal_user_test_company_token):
        """Test job creation with immediate posting"""
        today = date.today()
        next_month = today + timedelta(days=30)

        payload = {
            "title": "Frontend Developer",
            "description": "React developer position",
            "location": "Taipei, Taiwan",
            "salary_range": {"type": "annually", "currency": "TWD", "min": "1200000", "max": "1500000"},
            "company_name": "Test Corp",
            "posting_date": today.isoformat(),
            "expiration_date": next_month.isoformat(),
            "required_skills": ["React", "JavaScript", "TypeScript"]
        }

        response = client.post(
            JOBS_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_test_company_token}"
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "active"

    def test_create_job_invalid_dates_test_company_user(self, client, normal_user_test_company_token):
        """Test job creation with invalid dates"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        payload = {
            "title": "Backend Developer",
            "description": "Go developer position",
            "location": "Taipei, Taiwan",
            "salary_range": {"type": "annually", "currency": "TWD", "min": "1200000", "max": "1500000"},
            "company_name": "Test Corp",
            "posting_date": today.isoformat(),
            "expiration_date": yesterday.isoformat(),  # Expiration date before posting date
            "required_skills": ["Go", "Docker"]
        }

        response = client.post(
            JOBS_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_test_company_token}"
        )

        assert response.status_code == 422

    def test_create_job_missing_required_fields_test_company_user(self, client, normal_user_test_company_token):
        """Test job creation with missing required fields"""
        payload = {
            "title": "DevOps Engineer"
            # Missing other required fields
        }

        response = client.post(
            JOBS_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_test_company_token}"
        )

        assert response.status_code == 422

    @pytest.mark.django_db(transaction=True)
    def test_rate_limiting_test_company_user(self, client, normal_user_test_company_token):
        """Test API rate limiting"""
        tomorrow = date.today() + timedelta(days=1)
        next_month = date.today() + timedelta(days=30)
        payload = {
            "title": "Backend Engineer",
            "description": "Python developer position",
            "location": "Taipei, Taiwan",
            "salary_range": {"type": "annually", "currency": "TWD", "min": "1200000", "max": "1500000"},
            "company_name": "Test Corp",
            "posting_date": tomorrow.isoformat(),
            "expiration_date": next_month.isoformat(),
            "required_skills": ["Python", "Django", "REST API"]
        }

        # Send 20 requests (exceeding the 10/second limit)
        responses = []
        for _ in range(20):
            response = client.post(
                JOBS_ENDPOINT,
                data=json.dumps(payload),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {normal_user_test_company_token}"
            )
            responses.append(response)

        # Verify that at least one request was rate limited
        assert any(r.status_code == 429 for r in responses)


@pytest.mark.django_db
class TestJobListAPI:
    @pytest.fixture
    def create_test_jobs(self):
        """Create test job listings"""
        today = date.today()
        jobs = []

        # Create 10 test jobs with different attributes
        for i in range(10):
            job = Job.objects.create(
                title=f"Software Engineer {i}",
                description=f"Development position {i}",
                location="Taipei",
                salary_range={
                    "type": "annually",
                    "currency": "TWD",
                    "min": 800000 + (i * 100000),
                    "max": 1500000 + (i * 100000)
                },
                company_name=f"Tech Company {i}",
                posting_date=today + timedelta(days=i),
                expiration_date=today + timedelta(days=30 + i),
                required_skills=["Python", "Django", "React"],
                status="active"
            )
            jobs.append(job)
        return jobs

    def test_list_jobs_basic(self, client, create_test_jobs):
        """Test basic job listing without filters"""
        response = client.get(JOBS_ENDPOINT)

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 10
        assert len(data["data"]) == 10
        assert data["current_page"] == 1

    def test_list_jobs_pagination(self, client, create_test_jobs):
        """Test job listing pagination"""
        response = client.get(f"{JOBS_ENDPOINT}?page=2&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 10
        assert len(data["data"]) == 5
        assert data["current_page"] == 2
        assert data["page_size"] == 5

    def test_list_jobs_title_filter(self, client, create_test_jobs):
        """Test job listing with title filter"""
        response = client.get(
            f"{JOBS_ENDPOINT}?title=Engineer 0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    def test_list_jobs_description_filter(self, client, create_test_jobs):
        """Test job listing with description filter"""
        response = client.get(
            f"{JOBS_ENDPOINT}?description=position 0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    def test_list_jobs_company_name_filter(self, client, create_test_jobs):
        """Test job listing with company name filter"""
        response = client.get(
            f"{JOBS_ENDPOINT}?company_name=Company 0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    def test_list_jobs_active_status_filter(self, client, create_test_jobs):
        """Test job listing with active status filter"""
        response = client.get(f"{JOBS_ENDPOINT}?status=active")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 10

    def test_list_jobs_expired_status_filter(self, client, create_test_jobs):
        """Test job listing with expired status filter"""
        response = client.get(f"{JOBS_ENDPOINT}?status=expired")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0

    def test_list_jobs_scheduled_status_filter(self, client, create_test_jobs):
        """Test job listing with scheduled status filter"""
        response = client.get(f"{JOBS_ENDPOINT}?status=scheduled")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0

    def test_list_jobs_existed_location_filter(self, client, create_test_jobs):
        """Test job listing with existed location filter"""
        response = client.get(
            f"{JOBS_ENDPOINT}?location=Taipei"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 10

    def test_list_jobs_not_existed_location_filter(self, client, create_test_jobs):
        """Test job listing with not existed location filter"""
        response = client.get(
            f"{JOBS_ENDPOINT}?location=Tokyo"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0

    def test_list_jobs_skills_filter(self, client, create_test_jobs):
        """Test job listing with required skills filter"""
        response = client.get(
            f"{JOBS_ENDPOINT}?required_skills=Python&required_skills=React"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 10

    def test_list_jobs_skills_filter_no_results(self, client, create_test_jobs):
        """Test job listing with required skills filter"""
        response = client.get(
            f"{JOBS_ENDPOINT}?required_skills=Python&required_skills=Flask"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0

    def test_list_jobs_salary_filter_not_including_required_fields(self, client, create_test_jobs):
        """Test job listing with salary range filter not including required fields"""
        response = client.get(
            f"{JOBS_ENDPOINT}?min_salary=1000000&max_salary=2000000"
        )
        assert response.status_code == 400

    def test_list_jobs_salary_filter(self, client, create_test_jobs):
        """Test job listing with salary range filter"""
        response = client.get(
            f"{JOBS_ENDPOINT}?salary_type=annually&salary_currency=TWD&min_salary=800000&max_salary=850000"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    def test_list_jobs_posting_date_filters(self, client, create_test_jobs):
        """Test job listing with posting date filters"""
        today = date.today()
        response = client.get(
            f"{JOBS_ENDPOINT}?posting_date_start={today}&posting_date_end={today + timedelta(days=1)}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2

    def test_list_jobs_expiration_date_filters(self, client, create_test_jobs):
        """Test job listing with expiration date filters"""
        today = date.today()
        response = client.get(
            f"{JOBS_ENDPOINT}?expiration_date_start={today + timedelta(days=30)}&expiration_date_end={today + timedelta(days=31)}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2

    def test_list_jobs_ordering_posting_date(self, client, create_test_jobs):
        """Test job listing ordering"""
        # Test ascending order
        response = client.get(
            f"{JOBS_ENDPOINT}?order_by=posting_date&order_direction=asc"
        )

        assert response.status_code == 200
        data = response.json()
        posting_dates = [job["posting_date"] for job in data["data"]]
        assert posting_dates == sorted(posting_dates)

        # Test descending order
        response = client.get(
            f"{JOBS_ENDPOINT}?order_by=posting_date&order_direction=desc"
        )

        assert response.status_code == 200
        data = response.json()
        posting_dates = [job["posting_date"] for job in data["data"]]
        assert posting_dates == sorted(posting_dates, reverse=True)

    def test_list_jobs_ordering_expiration_date(self, client, create_test_jobs):
        """Test job listing ordering"""
        # Test ascending order
        response = client.get(
            f"{JOBS_ENDPOINT}?order_by=expiration_date&order_direction=asc"
        )

        assert response.status_code == 200
        data = response.json()
        expiration_dates = [job["expiration_date"] for job in data["data"]]
        assert expiration_dates == sorted(expiration_dates)

        # Test descending order
        response = client.get(
            f"{JOBS_ENDPOINT}?order_by=expiration_date&order_direction=desc"
        )

        assert response.status_code == 200
        data = response.json()
        expiration_dates = [job["expiration_date"] for job in data["data"]]
        assert expiration_dates == sorted(expiration_dates, reverse=True)

    def test_list_jobs_no_results(self, client, create_test_jobs):
        """Test job listing with filters that return no results"""
        response = client.get(
            f"{JOBS_ENDPOINT}?company_name=NonExistentCompany"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert len(data["data"]) == 0

    def test_rate_limiting(self, client):
        """Test API rate limiting"""
        # Send 21 requests (exceeding the 20/second limit)
        responses = []
        for _ in range(21):
            response = client.get(JOBS_ENDPOINT)
            responses.append(response)

        # Verify that at least one request was rate limited
        assert any(r.status_code == 429 for r in responses)


@pytest.mark.django_db
class TestJobDetailAPI:
    @pytest.fixture
    def test_job(self):
        """Create a test job for testing"""
        return Job.objects.create(
            title="Software Engineer",
            description="Python developer position",
            location="Taipei",
            salary_range={
                "type": "annually",
                "currency": "TWD",
                "min": 800000,
                "max": 1500000
            },
            company_name="Tech Company",
            posting_date=date.today(),
            expiration_date=date.today() + timedelta(days=30),
            required_skills=["Python", "Django", "React"]
        )

    def test_get_job_success(self, client, test_job):
        """Test successful retrieval of a job by ID"""
        response = client.get(f"{JOBS_ENDPOINT}/{test_job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_job.id
        assert data["title"] == test_job.title
        assert data["description"] == test_job.description
        assert data["location"] == test_job.location
        assert data["salary_range"] == test_job.salary_range
        assert data["company_name"] == test_job.company_name
        assert data["required_skills"] == test_job.required_skills
        assert data["status"] == test_job.status

    def test_get_job_not_found(self, client):
        """Test retrieval of non-existent job"""
        non_existent_id = 99999
        response = client.get(f"{JOBS_ENDPOINT}/{non_existent_id}")

        assert response.status_code == 404

    def test_get_job_invalid_id(self, client):
        """Test retrieval with invalid job ID format"""
        response = client.get(f"{JOBS_ENDPOINT}/invalid")

        assert response.status_code == 422  # Validation error

    def test_rate_limiting(self, client, test_job):
        """Test API rate limiting"""
        # Send 30 requests (exceeding the 20/second limit)
        responses = []
        for _ in range(30):
            response = client.get(f"{JOBS_ENDPOINT}/{test_job.id}")
            responses.append(response)

        # Verify that at least one request was rate limited
        assert any(r.status_code == 429 for r in responses)


@pytest.mark.django_db
class TestJobUpdateAPI:
    @pytest.fixture
    def test_job(self, normal_user_test_company):
        """Create a test job for testing"""
        return Job.objects.create(
            title="Software Engineer",
            description="Python developer position",
            location="Taipei",
            salary_range={
                "type": "annually",
                "currency": "TWD",
                "min": 800000,
                "max": 1500000
            },
            company_name="Test Corp",
            posting_date=date.today(),
            expiration_date=date.today() + timedelta(days=30),
            required_skills=["Python", "Django", "React"],
            status="active",
            created_by=normal_user_test_company,
            last_updated_by=normal_user_test_company
        )

    def test_update_job_success_test_superuser(self, client, test_job, superuser_token):
        """Test successful update of a job"""
        tomorrow = date.today() + timedelta(days=1)
        next_month = date.today() + timedelta(days=30)

        payload = {
            "title": "Senior Software Engineer",  # Changed title
            "description": "Updated position description",  # Changed description
            "location": "Taipei",
            "salary_range": {
                "type": "annually",
                "currency": "TWD",
                "min": "900000",  # Changed salary
                "max": "1600000"
            },
            "company_name": "Test Corp",  # Same company name
            "posting_date": tomorrow.isoformat(),
            "expiration_date": next_month.isoformat(),
            "required_skills": ["Python", "Django", "React", "AWS"]  # Added skill
        }

        response = client.put(
            f"{JOBS_ENDPOINT}/{test_job.id}",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["description"] == payload["description"]
        assert data["required_skills"] == payload["required_skills"]
        assert data["status"] == "scheduled"  # Should be scheduled as posting_date is tomorrow

    def test_update_job_success_test_company_user(self, client, test_job, normal_user_test_company_token):
        """Test successful update of a job"""
        tomorrow = date.today() + timedelta(days=1)
        next_month = date.today() + timedelta(days=30)

        payload = {
            "title": "Senior Software Engineer",  # Changed title
            "description": "Updated position description",  # Changed description
            "location": "Taipei",
            "salary_range": {
                "type": "annually",
                "currency": "TWD",
                "min": "900000",  # Changed salary
                "max": "1600000"
            },
            "company_name": "Test Corp",  # Same company name
            "posting_date": tomorrow.isoformat(),
            "expiration_date": next_month.isoformat(),
            "required_skills": ["Python", "Django", "React", "AWS"]  # Added skill
        }

        response = client.put(
            f"{JOBS_ENDPOINT}/{test_job.id}",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_test_company_token}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["description"] == payload["description"]
        assert data["required_skills"] == payload["required_skills"]
        assert data["status"] == "scheduled"  # Should be scheduled as posting_date is tomorrow

    def test_update_job_success_no_company_user(self, client, test_job, normal_user_no_company_token):
        """Test successful update of a job"""
        tomorrow = date.today() + timedelta(days=1)
        next_month = date.today() + timedelta(days=30)

        payload = {
            "title": "Senior Software Engineer",  # Changed title
            "description": "Updated position description",  # Changed description
            "location": "Taipei",
            "salary_range": {
                "type": "annually",
                "currency": "TWD",
                "min": "900000",  # Changed salary
                "max": "1600000"
            },
            "company_name": "Test Corp",  # Same company name
            "posting_date": tomorrow.isoformat(),
            "expiration_date": next_month.isoformat(),
            "required_skills": ["Python", "Django", "React", "AWS"]  # Added skill
        }

        response = client.put(
            f"{JOBS_ENDPOINT}/{test_job.id}",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_no_company_token}"
        )

        assert response.status_code == 403

    def test_update_job_company_name_change_test_company_user(self, client, test_job, normal_user_test_company_token):
        """Test attempt to change company name"""
        payload = {
            "title": test_job.title,
            "description": test_job.description,
            "location": test_job.location,
            "salary_range": test_job.salary_range,
            "company_name": "Different Company",  # Attempting to change company name
            "posting_date": test_job.posting_date.isoformat(),
            "expiration_date": test_job.expiration_date.isoformat(),
            "required_skills": test_job.required_skills
        }

        response = client.put(
            f"{JOBS_ENDPOINT}/{test_job.id}",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_test_company_token}"
        )

        assert response.status_code == 400

    def test_update_job_not_found_test_company_user(self, client, normal_user_test_company_token):
        """Test update of non-existent job"""
        payload = {
            "title": "Test Job",
            "description": "Test Description",
            "location": "Taipei",
            "salary_range": {
                "type": "annually",
                "currency": "TWD",
                "min": "800000",
                "max": "1500000"
            },
            "company_name": "Tech Company",
            "posting_date": date.today().isoformat(),
            "expiration_date": (date.today() + timedelta(days=30)).isoformat(),
            "required_skills": ["Python"]
        }

        response = client.put(
            f"{JOBS_ENDPOINT}/99999",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_test_company_token}"
        )

        assert response.status_code == 404

    def test_update_job_invalid_dates_test_company_user(self, client, test_job, normal_user_test_company_token):
        """Test update with invalid dates"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        payload = {
            "title": test_job.title,
            "description": test_job.description,
            "location": test_job.location,
            "salary_range": test_job.salary_range,
            "company_name": test_job.company_name,
            "posting_date": today.isoformat(),
            "expiration_date": yesterday.isoformat(),  # Invalid: expiration before posting
            "required_skills": test_job.required_skills
        }

        response = client.put(
            f"{JOBS_ENDPOINT}/{test_job.id}",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_test_company_token}"
        )

        assert response.status_code == 422

    def test_update_job_missing_required_fields_test_company_user(self, client, test_job,
                                                                  normal_user_test_company_token):
        """Test update with missing required fields"""
        payload = {
            "title": "Updated Title"
            # Missing other required fields
        }

        response = client.put(
            f"{JOBS_ENDPOINT}/{test_job.id}",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_test_company_token}"
        )

        assert response.status_code == 422

    def test_rate_limiting_test_company_user(self, client, test_job, normal_user_test_company_token):
        """Test API rate limiting"""
        payload = {
            "title": test_job.title,
            "description": test_job.description,
            "location": test_job.location,
            "salary_range": test_job.salary_range,
            "company_name": test_job.company_name,
            "posting_date": test_job.posting_date.isoformat(),
            "expiration_date": test_job.expiration_date.isoformat(),
            "required_skills": test_job.required_skills
        }

        # Send 20 requests (exceeding the 10/second limit)
        responses = []
        for _ in range(20):
            response = client.put(
                f"{JOBS_ENDPOINT}/{test_job.id}",
                data=json.dumps(payload),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {normal_user_test_company_token}"
            )
            responses.append(response)

        # Verify that at least one request was rate limited
        assert any(r.status_code == 429 for r in responses)


@pytest.mark.django_db
class TestJobDeletionAPI:
    @pytest.fixture
    def test_job(self):
        """Create a test job for testing"""
        return Job.objects.create(
            title="Software Engineer",
            description="Python developer position",
            location="Taipei",
            salary_range={
                "type": "annually",
                "currency": "TWD",
                "min": 800000,
                "max": 1500000
            },
            company_name="Tech Company",
            posting_date=date.today(),
            expiration_date=date.today() + timedelta(days=30),
            required_skills=["Python", "Django", "React"]
        )

    def test_delete_job_success(self, client, test_job):
        """Test successful deletion of a job by ID"""
        response = client.delete(f"{JOBS_ENDPOINT}/{test_job.id}")

        assert response.status_code == 204

        # Verify that the job no longer exists
        assert not Job.objects.filter(id=test_job.id).exists()

    def test_delete_job_not_found(self, client):
        """Test deletion of non-existent job"""
        non_existent_id = 99999
        response = client.delete(f"{JOBS_ENDPOINT}/{non_existent_id}")

        assert response.status_code == 404

    def test_delete_job_invalid_id(self, client):
        """Test deletion with invalid job ID format"""
        response = client.delete(f"{JOBS_ENDPOINT}/invalid")

        assert response.status_code == 422  # Validation error

    def test_rate_limiting(self, client, test_job):
        """Test API rate limiting"""
        # Send 6 requests (exceeding the 5/second limit)
        responses = []
        for _ in range(6):
            response = client.delete(f"{JOBS_ENDPOINT}/{test_job.id}")
            responses.append(response)

        # Verify that at least one request was rate limited
        assert any(r.status_code == 429 for r in responses)
