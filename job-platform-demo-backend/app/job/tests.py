import pytest
from datetime import date, timedelta
import json
from django.core.cache import cache

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
