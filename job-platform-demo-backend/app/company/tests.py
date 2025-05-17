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


@pytest.mark.django_db
class TestCompanyDeletionAPI:
    def test_delete_company_success(self, client):
        """Test successful company deletion"""
        # Create a company to delete
        company = Company.objects.create(name="Company To Delete")

        response = client.delete(f"{COMPANIES_ENDPOINT}/{company.id}")

        assert response.status_code == 204

        # Verify company was deleted from database
        with pytest.raises(Company.DoesNotExist):
            Company.objects.get(id=company.id)

    def test_delete_company_not_found(self, client):
        """Test deleting non-existent company"""
        non_existent_id = 99999

        response = client.delete(f"{COMPANIES_ENDPOINT}/{non_existent_id}")

        assert response.status_code == 404
