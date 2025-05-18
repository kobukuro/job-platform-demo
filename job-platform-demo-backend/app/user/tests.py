import pytest
from company.models import Company, CompanyDomain
from user.models import User

USER_ENDPOINT = "/users"
LOGIN_ENDPOINT = "/users/login"


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


@pytest.mark.django_db
class TestUserLoginAPI:
    def test_login_successful(self, client):
        """Test successful user login"""
        # Create test user
        test_user = User.objects.create_user(
            email="test@example.com",
            password="securePassword123"
        )

        payload = {
            "email": "test@example.com",
            "password": "securePassword123"
        }

        response = client.post(
            LOGIN_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        # Create test user
        test_user = User.objects.create_user(
            email="test@example.com",
            password="correctPassword123"
        )

        # Try with wrong password
        payload = {
            "email": "test@example.com",
            "password": "wrongPassword123"
        }

        response = client.post(
            LOGIN_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        payload = {
            "email": "nonexistent@example.com",
            "password": "anyPassword123"
        }

        response = client.post(
            LOGIN_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """Test login request with missing required fields"""
        # Missing password
        payload = {
            "email": "test@example.com"
        }

        response = client.post(
            LOGIN_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        assert response.status_code == 422

    def test_login_empty_fields(self, client):
        """Test login with empty fields"""
        payload = {
            "email": "",
            "password": ""
        }

        response = client.post(
            LOGIN_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        assert response.status_code == 422

    def test_login_malformed_json(self, client):
        """Test login with malformed JSON"""
        response = client.post(
            LOGIN_ENDPOINT,
            data="invalid json",
            content_type="application/json"
        )

        assert response.status_code == 400

    def test_login_last_login_updated(self, client):
        """Test that last_login timestamp is updated upon successful login"""
        # Create test user
        test_user = User.objects.create_user(
            email="test@example.com",
            password="securePassword123"
        )

        initial_last_login = test_user.last_login

        payload = {
            "email": "test@example.com",
            "password": "securePassword123"
        }

        response = client.post(
            LOGIN_ENDPOINT,
            data=payload,
            content_type="application/json"
        )

        # Refresh user from database
        test_user.refresh_from_db()
        assert test_user.last_login is not None
        assert test_user.last_login != initial_last_login
