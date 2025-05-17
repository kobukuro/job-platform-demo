import pytest
from datetime import date, timedelta
import json
from django.core.cache import cache
from job.models import Job

JOBS_ENDPOINT = "/jobs"


@pytest.mark.django_db
class TestJobCreationAPI:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """
        Setup method that runs before each test method.
        Clears the cache before and after each test.
        """
        cache.clear()
        yield
        cache.clear()

    def test_create_job_success_scheduled(self, client):
        """Test successful job creation with scheduled posting"""
        tomorrow = date.today() + timedelta(days=1)
        next_month = date.today() + timedelta(days=30)

        payload = {
            "title": "Backend Engineer",
            "description": "Python developer position",
            "location": "Taipei, Taiwan",
            "salary_range": {"type": "annually", "currency": "TWD", "min": "1200000", "max": "1500000"},
            "company_name": "Tech Corp",
            "posting_date": tomorrow.isoformat(),
            "expiration_date": next_month.isoformat(),
            "required_skills": ["Python", "Django", "REST API"]
        }

        response = client.post(
            JOBS_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["status"] == "scheduled"

    def test_create_job_immediate_posting(self, client):
        """Test job creation with immediate posting"""
        today = date.today()
        next_month = today + timedelta(days=30)

        payload = {
            "title": "Frontend Developer",
            "description": "React developer position",
            "location": "Taipei, Taiwan",
            "salary_range": {"type": "annually", "currency": "TWD", "min": "1200000", "max": "1500000"},
            "company_name": "Web Corp",
            "posting_date": today.isoformat(),
            "expiration_date": next_month.isoformat(),
            "required_skills": ["React", "JavaScript", "TypeScript"]
        }

        response = client.post(
            JOBS_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "active"

    def test_create_job_invalid_dates(self, client):
        """Test job creation with invalid dates"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        payload = {
            "title": "Backend Developer",
            "description": "Go developer position",
            "location": "Taipei, Taiwan",
            "salary_range": {"type": "annually", "currency": "TWD", "min": "1200000", "max": "1500000"},
            "company_name": "Backend Corp",
            "posting_date": today.isoformat(),
            "expiration_date": yesterday.isoformat(),  # Expiration date before posting date
            "required_skills": ["Go", "Docker"]
        }

        response = client.post(
            JOBS_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 422

    def test_create_job_missing_required_fields(self, client):
        """Test job creation with missing required fields"""
        payload = {
            "title": "DevOps Engineer"
            # Missing other required fields
        }

        response = client.post(
            JOBS_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 422

    @pytest.mark.django_db(transaction=True)
    def test_rate_limiting(self, client):
        """Test API rate limiting"""
        tomorrow = date.today() + timedelta(days=1)
        next_month = date.today() + timedelta(days=30)
        payload = {
            "title": "Backend Engineer",
            "description": "Python developer position",
            "location": "Taipei, Taiwan",
            "salary_range": {"type": "annually", "currency": "TWD", "min": "1200000", "max": "1500000"},
            "company_name": "Tech Corp",
            "posting_date": tomorrow.isoformat(),
            "expiration_date": next_month.isoformat(),
            "required_skills": ["Python", "Django", "REST API"]
        }

        # Send 11 requests (exceeding the 10/second limit)
        responses = []
        for _ in range(11):
            response = client.post(
                JOBS_ENDPOINT,
                data=json.dumps(payload),
                content_type="application/json"
            )
            responses.append(response)

        # Verify that at least one request was rate limited
        assert any(r.status_code == 429 for r in responses)


@pytest.mark.django_db
class TestJobListAPI:

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """
        Setup method that runs before each test method.
        Clears the cache before and after each test.
        """
        cache.clear()
        yield
        cache.clear()

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
