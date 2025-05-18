import json

import pytest
from django.contrib.auth import get_user_model
from company.models import Company, CompanyDomain

User = get_user_model()
COMPANIES_ENDPOINT = "/companies"
LOGIN_ENDPOINT = "/users/login"


@pytest.fixture
def superuser_credentials():
    return {
        "email": "admin@test.com",
        "password": "password123"
    }


@pytest.fixture
def normal_user_credentials():
    return {
        "email": "user@test.com",
        "password": "password123"
    }


@pytest.fixture
def superuser(superuser_credentials):
    return User.objects.create_superuser(
        email=superuser_credentials["email"],
        password=superuser_credentials["password"]
    )


@pytest.fixture
def normal_user(normal_user_credentials):
    return User.objects.create_user(
        email=normal_user_credentials["email"],
        password=normal_user_credentials["password"]
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
def normal_user_token(client, normal_user, normal_user_credentials):
    response = client.post(
        LOGIN_ENDPOINT,
        data=json.dumps(normal_user_credentials),
        content_type="application/json"
    )
    return response.json()["access_token"]


@pytest.mark.django_db
class TestCompanyCreationAPI:
    def test_create_company_success_as_superuser(self, client, superuser_token):
        """Test successful company creation"""
        payload = {
            "name": "Test Company"
        }

        response = client.post(
            COMPANIES_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]

        # Verify company was created in database
        company = Company.objects.get(name=payload["name"])
        assert company is not None

    def test_create_company_forbidden_as_normal_user(self, client, normal_user_token):
        """Test company creation forbidden for normal user"""
        payload = {"name": "Test Company"}

        response = client.post(
            COMPANIES_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_token}"
        )

        assert response.status_code == 403

    def test_create_company_unauthorized(self, client):
        """Test company creation without authorization"""
        payload = {"name": "Test Company"}

        response = client.post(
            COMPANIES_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 401

    def test_create_company_duplicate_name_as_superuser(self, client, superuser_token):
        """Test creating company with duplicate name"""
        # Create initial company
        Company.objects.create(name="Existing Company")

        payload = {
            "name": "Existing Company"  # Use same name
        }

        response = client.post(
            COMPANIES_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 409

    def test_create_company_empty_name_as_superuser(self, client, superuser_token):
        """Test creating company with empty name"""
        payload = {
            "name": ""
        }

        response = client.post(
            COMPANIES_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 422

    def test_create_company_missing_required_fields_as_superuser(self, client, superuser_token):
        """Test creating company with missing required fields"""
        payload = {}  # Missing name field

        response = client.post(
            COMPANIES_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.django_db
class TestCompanyDeletionAPI:
    def test_delete_company_success_as_superuser(self, client, superuser_token):
        """Test successful company deletion"""
        # Create a company to delete
        company = Company.objects.create(name="Company To Delete")

        response = client.delete(f"{COMPANIES_ENDPOINT}/{company.id}",
                                 HTTP_AUTHORIZATION=f"Bearer {superuser_token}")

        assert response.status_code == 204

        # Verify company was deleted from database
        with pytest.raises(Company.DoesNotExist):
            Company.objects.get(id=company.id)

    def test_delete_company_forbidden_as_normal_user(self, client, normal_user_token):
        """Test company deletion forbidden for normal user"""
        company = Company.objects.create(name="Company To Delete")

        response = client.delete(
            f"{COMPANIES_ENDPOINT}/{company.id}",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_token}"
        )

        assert response.status_code == 403

    def test_delete_company_unauthorized(self, client):
        """Test company deletion without authorization"""
        company = Company.objects.create(name="Company To Delete")

        response = client.delete(
            f"{COMPANIES_ENDPOINT}/{company.id}"
        )

        assert response.status_code == 401

    def test_delete_company_not_found_as_superuser(self, client, superuser_token):
        """Test deleting non-existent company"""
        non_existent_id = 99999

        response = client.delete(f"{COMPANIES_ENDPOINT}/{non_existent_id}",
                                 HTTP_AUTHORIZATION=f"Bearer {superuser_token}")

        assert response.status_code == 404


@pytest.mark.django_db
class TestDomainCreationAPI:
    def test_create_domain_success_as_superuser(self, client, superuser_token):
        """Test successful domain creation"""
        # Create a company first
        company = Company.objects.create(name="Test Company")

        payload = {
            "name": "test.com"
        }

        response = client.post(
            f"{COMPANIES_ENDPOINT}/{company.id}/domains",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 201

        # Verify domain was created in database
        domain = CompanyDomain.objects.get(name=payload["name"])
        assert domain is not None
        assert domain.company_id == company.id

    def test_create_domain_forbidden_as_normal_user(self, client, normal_user_token):
        """Test domain creation forbidden for normal user"""
        company = Company.objects.create(name="Test Company")
        payload = {"name": "test.com"}

        response = client.post(
            f"{COMPANIES_ENDPOINT}/{company.id}/domains",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_token}"
        )

        assert response.status_code == 403

    def test_create_domain_unauthorized(self, client):
        """Test domain creation without authorization"""
        company = Company.objects.create(name="Test Company")
        payload = {"name": "test.com"}

        response = client.post(
            f"{COMPANIES_ENDPOINT}/{company.id}/domains",
            data=json.dumps(payload),
            content_type="application/json"
        )

        assert response.status_code == 401

    def test_create_domain_company_not_found_as_superuser(self, client, superuser_token):
        """Test creating domain for non-existent company"""
        non_existent_id = 99999

        payload = {
            "name": "test.com"
        }

        response = client.post(
            f"{COMPANIES_ENDPOINT}/{non_existent_id}/domains",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 404

    def test_create_duplicate_domain_as_superuser(self, client, superuser_token):
        """Test creating domain with duplicate name"""
        # Create two companies
        company1 = Company.objects.create(name="Company 1")
        company2 = Company.objects.create(name="Company 2")

        # Create domain for first company
        CompanyDomain.objects.create(name="test.com", company=company1)

        # Try to create same domain for second company
        payload = {
            "name": "test.com"
        }

        response = client.post(
            f"{COMPANIES_ENDPOINT}/{company2.id}/domains",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 409

    def test_create_domain_empty_name_as_superuser(self, client, superuser_token):
        """Test creating domain with empty name"""
        company = Company.objects.create(name="Test Company")

        payload = {
            "name": ""
        }

        response = client.post(
            f"{COMPANIES_ENDPOINT}/{company.id}/domains",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 422


@pytest.mark.django_db
class TestDomainDeletionAPI:
    def test_delete_domain_success_as_superuser(self, client, superuser_token):
        """Test successful domain deletion"""
        company = Company.objects.create(name="Test Company")
        domain = CompanyDomain.objects.create(
            name="test.com",
            company=company
        )

        response = client.delete(
            f"{COMPANIES_ENDPOINT}/{company.id}/domains/{domain.id}",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 204

        # Verify domain was deleted from database
        with pytest.raises(CompanyDomain.DoesNotExist):
            CompanyDomain.objects.get(id=domain.id)

    def test_delete_domain_forbidden_as_normal_user(self, client, normal_user_token):
        """Test domain deletion forbidden for normal user"""
        company = Company.objects.create(name="Test Company")
        domain = CompanyDomain.objects.create(name="test.com", company=company)

        response = client.delete(
            f"{COMPANIES_ENDPOINT}/{company.id}/domains/{domain.id}",
            HTTP_AUTHORIZATION=f"Bearer {normal_user_token}"
        )

        assert response.status_code == 403

    def test_delete_domain_unauthorized(self, client):
        """Test domain deletion without authorization"""
        company = Company.objects.create(name="Test Company")
        domain = CompanyDomain.objects.create(name="test.com", company=company)

        response = client.delete(
            f"{COMPANIES_ENDPOINT}/{company.id}/domains/{domain.id}"
        )

        assert response.status_code == 401

    def test_delete_domain_company_not_found_as_superuser(self, client, superuser_token):
        """Test deleting domain when company doesn't exist"""
        non_existent_company_id = 99999
        domain_id = 1

        response = client.delete(
            f"{COMPANIES_ENDPOINT}/{non_existent_company_id}/domains/{domain_id}",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Company not found"

    def test_delete_domain_not_found_as_superuser(self, client, superuser_token):
        """Test deleting non-existent domain"""
        company = Company.objects.create(name="Test Company")
        non_existent_domain_id = 99999

        response = client.delete(
            f"{COMPANIES_ENDPOINT}/{company.id}/domains/{non_existent_domain_id}",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Domain not found"

    def test_delete_domain_wrong_company_as_superuser(self, client, superuser_token):
        """Test deleting domain that belongs to different company"""
        company1 = Company.objects.create(name="Company 1")
        company2 = Company.objects.create(name="Company 2")

        domain = CompanyDomain.objects.create(
            name="test.com",
            company=company1
        )

        response = client.delete(
            f"{COMPANIES_ENDPOINT}/{company2.id}/domains/{domain.id}",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Domain not found"

    def test_delete_domain_invalid_company_id_as_superuser(self, client, superuser_token):
        """Test deleting domain with invalid company ID format"""
        response = client.delete(
            f"{COMPANIES_ENDPOINT}/invalid/domains/1",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 422  # Validation error

    def test_delete_domain_invalid_domain_id_as_superuser(self, client, superuser_token):
        """Test deleting domain with invalid domain ID format"""
        company = Company.objects.create(name="Test Company")

        response = client.delete(
            f"{COMPANIES_ENDPOINT}/{company.id}/domains/invalid",
            HTTP_AUTHORIZATION=f"Bearer {superuser_token}"
        )

        assert response.status_code == 422  # Validation error
