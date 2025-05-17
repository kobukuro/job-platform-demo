import pytest
import json
from django.core.cache import cache
from company.models import Company

COMPANIES_ENDPOINT = "/companies"


@pytest.mark.django_db
class TestCompanyCreationAPI:
    def test_create_company_success(self, client):
        """Test successful company creation"""
        payload = {
            "name": "Test Company"
        }

        response = client.post(
            COMPANIES_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]

        # Verify company was created in database
        company = Company.objects.get(name=payload["name"])
        assert company is not None

    def test_create_company_duplicate_name(self, client):
        """Test creating company with duplicate name"""
        # Create initial company
        Company.objects.create(name="Existing Company")

        payload = {
            "name": "Existing Company"  # Use same name
        }

        response = client.post(
            COMPANIES_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 409

    def test_create_company_empty_name(self, client):
        """Test creating company with empty name"""
        payload = {
            "name": ""
        }

        response = client.post(
            COMPANIES_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 422

    def test_create_company_missing_required_fields(self, client):
        """Test creating company with missing required fields"""
        payload = {}  # Missing name field

        response = client.post(
            COMPANIES_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 422  # Validation error
