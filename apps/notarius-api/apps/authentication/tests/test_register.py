"""
Tests for the registration endpoint with cartório support
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.tenancy.models import Tenant, RegistryRequest

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant():
    return Tenant.objects.create(
        nome="Cartório de Teste",
        uf="SP",
        municipio="São Paulo",
        tipo="1º Ofício"
    )


@pytest.mark.django_db
class TestRegisterEndpoint:
    """Test registration with cartório support"""

    def test_register_with_cartorio_id(self, api_client, tenant):
        """Test registration with a valid cartorio_id creates ACTIVE membership"""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
            "cartorio_id": str(tenant.id),
        }

        response = api_client.post("/api/v1/auth/register/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "ACTIVE"
        assert response.data["redirect"] == "/app"
        assert "token" in response.data
        assert "user" in response.data

        # Verify user was created
        user = User.objects.get(email="test@example.com")
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"

        # Verify tenant membership
        assert user.profile.default_tenant == tenant
        assert tenant in user.profile.tenants.all()

    def test_register_without_cartorio_id(self, api_client):
        """Test registration without cartorio_id returns NO_CARTORIO status"""
        data = {
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        response = api_client.post("/api/v1/auth/register/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "NO_CARTORIO"
        assert response.data["redirect"] == "/onboarding/pending-cartorio"
        assert "token" in response.data
        assert "user" in response.data

        # Verify user was created
        user = User.objects.get(email="test2@example.com")
        assert user.profile.default_tenant is None
        assert user.profile.tenants.count() == 0

    def test_register_with_invalid_cartorio_id(self, api_client):
        """Test registration with invalid cartorio_id returns error"""
        import uuid
        data = {
            "username": "testuser3",
            "email": "test3@example.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
            "cartorio_id": str(uuid.uuid4()),
        }

        response = api_client.post("/api/v1/auth/register/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cartório not found" in str(response.data.get("detail", ""))

    def test_register_with_hashed_cpf_phone(self, api_client, tenant):
        """Test registration with hashed CPF and phone"""
        cpf_hash = "a" * 64  # Valid SHA256 hex string
        phone_hash = "b" * 64

        data = {
            "username": "testuser4",
            "email": "test4@example.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
            "cartorio_id": str(tenant.id),
            "cpf_hash": cpf_hash,
            "phone_hash": phone_hash,
        }

        response = api_client.post("/api/v1/auth/register/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "ACTIVE"

    def test_register_with_invalid_hash_length(self, api_client):
        """Test registration with invalid hash length returns error"""
        data = {
            "username": "testuser5",
            "email": "test5@example.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
            "cpf_hash": "invalid",  # Too short
        }

        response = api_client.post("/api/v1/auth/register/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, api_client):
        """Test registration with duplicate email returns error"""
        User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="pass123"
        )

        data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        response = api_client.post("/api/v1/auth/register/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data


@pytest.mark.django_db
class TestTenantSearchEndpoint:
    """Test tenant search endpoint"""

    def test_search_tenants(self, api_client):
        """Test searching tenants by name"""
        Tenant.objects.create(
            nome="Cartório Central",
            uf="SP",
            municipio="São Paulo",
            tipo="1º Ofício"
        )
        Tenant.objects.create(
            nome="Cartório de Registro",
            uf="RJ",
            municipio="Rio de Janeiro",
            tipo="2º Ofício"
        )

        response = api_client.get("/api/v1/tenancy/tenants/search/?q=Central")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["nome"] == "Cartório Central"

    def test_search_tenants_with_uf_filter(self, api_client):
        """Test searching tenants with UF filter"""
        Tenant.objects.create(
            nome="Cartório SP",
            uf="SP",
            municipio="São Paulo",
        )
        Tenant.objects.create(
            nome="Cartório RJ",
            uf="RJ",
            municipio="Rio de Janeiro",
        )

        response = api_client.get("/api/v1/tenancy/tenants/search/?q=Cartório&uf=SP")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["uf"] == "SP"

    def test_search_tenants_empty_query(self, api_client):
        """Test searching with empty query returns empty results"""
        Tenant.objects.create(
            nome="Cartório Test",
            uf="SP",
        )

        response = api_client.get("/api/v1/tenancy/tenants/search/?q=")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_search_tenants_limit(self, api_client):
        """Test search respects limit parameter"""
        for i in range(25):
            Tenant.objects.create(
                nome=f"Cartório {i}",
                uf="SP",
            )

        response = api_client.get("/api/v1/tenancy/tenants/search/?q=Cartório&limit=10")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) <= 10


@pytest.mark.django_db
class TestTenantRequestEndpoint:
    """Test tenant request endpoint"""

    def test_create_tenant_request(self, api_client):
        """Test creating a new tenant request"""
        data = {
            "nome": "Novo Cartório",
            "municipio": "Brasília",
            "uf": "DF",
            "note": "Solicitação de inclusão"
        }

        response = api_client.post("/api/v1/tenancy/tenants/request-new/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "request_id" in response.data

        # Verify request was created
        request_id = response.data["request_id"]
        registry_request = RegistryRequest.objects.get(id=request_id)
        assert registry_request.nome == "Novo Cartório"
        assert registry_request.municipio == "Brasília"
        assert registry_request.uf == "DF"
        assert registry_request.note == "Solicitação de inclusão"

    def test_create_tenant_request_without_note(self, api_client):
        """Test creating tenant request without optional note"""
        data = {
            "nome": "Outro Cartório",
            "municipio": "São Paulo",
            "uf": "SP",
        }

        response = api_client.post("/api/v1/tenancy/tenants/request-new/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "request_id" in response.data

    def test_create_tenant_request_invalid_data(self, api_client):
        """Test creating tenant request with invalid data returns error"""
        data = {
            "nome": "",  # Empty nome
            "municipio": "São Paulo",
            "uf": "SP",
        }

        response = api_client.post("/api/v1/tenancy/tenants/request-new/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

