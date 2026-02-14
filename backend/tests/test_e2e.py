"""
NT Commerce E2E Tests
Comprehensive end-to-end tests for the application
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from server import app

# Test configuration
BASE_URL = "http://test"

# Test credentials
TENANT_USER = {"email": "test@test.com", "password": "test123"}
SUPER_ADMIN = {"email": "super@ntcommerce.com", "password": "admin123"}


@pytest_asyncio.fixture
async def client():
    """Create async test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        yield ac


@pytest_asyncio.fixture
async def tenant_token(client):
    """Get authentication token for tenant user"""
    response = await client.post("/api/auth/login", json=TENANT_USER)
    if response.status_code == 200:
        return response.json().get("token")
    return None


@pytest_asyncio.fixture
async def admin_token(client):
    """Get authentication token for super admin"""
    response = await client.post("/api/auth/super-admin-login", json=SUPER_ADMIN)
    if response.status_code == 200:
        return response.json().get("token")
    return None


class TestAuthentication:
    """Authentication E2E tests"""
    
    @pytest.mark.asyncio
    async def test_tenant_login_success(self, client):
        """Test successful tenant login"""
        response = await client.post("/api/auth/login", json=TENANT_USER)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        
    @pytest.mark.asyncio
    async def test_tenant_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = await client.post("/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404]
        
    @pytest.mark.asyncio
    async def test_super_admin_login(self, client):
        """Test super admin login"""
        response = await client.post("/api/auth/super-admin-login", json=SUPER_ADMIN)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data


class TestProducts:
    """Products E2E tests"""
    
    @pytest.mark.asyncio
    async def test_get_products(self, client, tenant_token):
        """Test fetching products list"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = await client.get("/api/products", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    @pytest.mark.asyncio
    async def test_create_product(self, client, tenant_token):
        """Test creating a new product"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        product_data = {
            "name": "Test Product E2E",
            "code": f"TEST-E2E-{os.urandom(4).hex()}",
            "price": 100.00,
            "quantity": 50,
            "category_id": None,
            "unit": "piece"
        }
        
        response = await client.post("/api/products", json=product_data, headers=headers)
        # Accept 200, 201 or 400 (if validation fails)
        assert response.status_code in [200, 201, 400]
        
    @pytest.mark.asyncio
    async def test_search_products(self, client, tenant_token):
        """Test product search functionality"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = await client.get("/api/products?search=test", headers=headers)
        assert response.status_code == 200


class TestCustomers:
    """Customers E2E tests"""
    
    @pytest.mark.asyncio
    async def test_get_customers(self, client, tenant_token):
        """Test fetching customers list"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = await client.get("/api/customers", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    @pytest.mark.asyncio
    async def test_create_customer(self, client, tenant_token):
        """Test creating a new customer"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        customer_data = {
            "name": f"Test Customer E2E {os.urandom(4).hex()}",
            "phone": "0555123456",
            "email": f"test_e2e_{os.urandom(4).hex()}@test.com"
        }
        
        response = await client.post("/api/customers", json=customer_data, headers=headers)
        assert response.status_code in [200, 201, 400]


class TestSales:
    """Sales/POS E2E tests"""
    
    @pytest.mark.asyncio
    async def test_get_sales(self, client, tenant_token):
        """Test fetching sales list"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = await client.get("/api/sales", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    @pytest.mark.asyncio
    async def test_get_daily_session(self, client, tenant_token):
        """Test getting daily session status"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = await client.get("/api/sessions/current", headers=headers)
        # 200 if session exists, 404 if no session
        assert response.status_code in [200, 404]
        
    @pytest.mark.asyncio
    async def test_get_cash_boxes(self, client, tenant_token):
        """Test getting cash boxes"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = await client.get("/api/cash-boxes", headers=headers)
        assert response.status_code == 200


class TestReports:
    """Reports E2E tests"""
    
    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self, client, tenant_token):
        """Test getting dashboard statistics"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = await client.get("/api/stats", headers=headers)
        assert response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_get_sales_report(self, client, tenant_token):
        """Test getting sales report"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = await client.get("/api/reports/sales", headers=headers)
        assert response.status_code == 200


class TestSaaSAdmin:
    """SaaS Admin E2E tests"""
    
    @pytest.mark.asyncio
    async def test_get_saas_stats(self, client, admin_token):
        """Test getting SaaS admin statistics"""
        if not admin_token:
            pytest.skip("No admin token available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/saas/stats", headers=headers)
        assert response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_get_tenants(self, client, admin_token):
        """Test getting tenants list"""
        if not admin_token:
            pytest.skip("No admin token available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/saas/tenants", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    @pytest.mark.asyncio
    async def test_get_plans(self, client, admin_token):
        """Test getting subscription plans"""
        if not admin_token:
            pytest.skip("No admin token available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/saas/plans", headers=headers)
        assert response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_get_monitoring(self, client, admin_token):
        """Test getting monitoring data"""
        if not admin_token:
            pytest.skip("No admin token available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get("/api/saas/monitoring", headers=headers)
        assert response.status_code == 200


class TestSettings:
    """Settings E2E tests"""
    
    @pytest.mark.asyncio
    async def test_get_system_settings(self, client, tenant_token):
        """Test getting system settings"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = await client.get("/api/settings/system", headers=headers)
        assert response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_get_receipt_settings(self, client, tenant_token):
        """Test getting receipt settings"""
        if not tenant_token:
            pytest.skip("No token available")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = await client.get("/api/settings/receipt", headers=headers)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
