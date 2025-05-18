import pytest
from company.models import Company, CompanyDomain

USER_ENDPOINT = "/users"


@pytest.mark.django_db
class TestUserRegistrationAPI:
    def test_register_user_with_company_domain(self, client):
        """Test user registration with company domain"""
        # Create test company and domain
        company = Company.objects.create(name="Test Company")
        CompanyDomain.objects.create(name="example.com", company=company)

        payload = {
            "email": "test@example.com",
            "password": "securePassword123"
        }

        response = client.post(
            USER_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["company_id"] == company.id

    def test_register_user_with_unknown_domain(self, client):
        """Test user registration with unknown domain"""
        payload = {
            "email": "test@unknown-domain.com",
            "password": "securePassword123"
        }

        response = client.post(
            USER_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["company_id"] is None

    def test_register_user_duplicate_email(self, client):
        """Test registration with duplicate email"""
        payload = {
            "email": "test@example.com",
            "password": "securePassword123"
        }

        # First registration
        client.post(
            USER_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        # Attempt to register with the same email
        response = client.post(
            USER_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        assert response.status_code == 409

    def test_register_user_invalid_email(self, client):
        """Test registration with invalid email format"""
        payload = {
            "email": "invalid-email",
            "password": "securePassword123"
        }

        response = client.post(
            USER_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        assert response.status_code == 422  # Validation error

    def test_register_user_missing_fields(self, client):
        """Test registration with missing required fields"""
        # Missing password
        payload = {
            "email": "test@example.com"
        }

        response = client.post(
            USER_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        assert response.status_code == 422

    def test_register_user_empty_fields(self, client):
        """Test registration with empty fields"""
        payload = {
            "email": "",
            "password": ""
        }

        response = client.post(
            USER_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        assert response.status_code == 422

    def test_register_user_malformed_json(self, client):
        """Test registration with malformed JSON"""
        response = client.post(
            USER_ENDPOINT,
            data="invalid json",
            content_type="application/json"
        )

        assert response.status_code == 400
