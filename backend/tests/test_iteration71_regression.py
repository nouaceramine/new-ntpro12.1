"""
NT Commerce 12.0 - Iteration 71 Regression Testing
Tests for major architectural change: server.py -> main.py migration
All application code moved to main.py, server.py is now just 'from main import app'
Also tests 4 new extracted route modules: online_store, sendgrid_email, sms_marketing, stripe
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TENANT_EMAIL = "ncr@ntcommerce.com"
TENANT_PASSWORD = "Test@123"
SUPER_ADMIN_EMAIL = "admin@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "Admin@2024"


class TestHealthAndSystemInfo:
    """Basic health and system endpoints - verify server is running after migration"""
    
    def test_health_endpoint(self):
        """GET /api/health - Basic health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Health response: {response.status_code} - {response.text[:200]}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_system_info(self):
        """GET /api/system/info - Version and table count"""
        response = requests.get(f"{BASE_URL}/api/system/info")
        print(f"System info response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data or "tables" in data
        # Note: 152 tables mentioned in requirements


class TestUnifiedLogin:
    """Test unified login for both tenant and super admin users"""
    
    def test_tenant_login(self):
        """POST /api/auth/unified-login with tenant credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        print(f"Tenant login response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data, f"Missing access_token in response: {data}"
        assert data.get("user_type") == "tenant"
        print(f"Tenant login successful - user_type: {data.get('user_type')}")
    
    def test_super_admin_login(self):
        """POST /api/auth/unified-login with super admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        print(f"Super admin login response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data, f"Missing access_token in response: {data}"
        # Super admin can be 'admin' type
        print(f"Super admin login successful - user_type: {data.get('user_type')}")
    
    def test_invalid_login(self):
        """POST /api/auth/unified-login with invalid credentials - should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


@pytest.fixture
def tenant_token():
    """Get tenant authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
        "email": TENANT_EMAIL,
        "password": TENANT_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Tenant authentication failed")


@pytest.fixture
def super_admin_token():
    """Get super admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Super admin authentication failed")


class TestProductsAPI:
    """Test products endpoint - core functionality"""
    
    def test_get_products_with_tenant_token(self, tenant_token):
        """GET /api/products (with tenant token) returns product list"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        print(f"Products response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # Should return list of products
        assert isinstance(data, list)
        print(f"Found {len(data)} products")


class TestOnlineStoreRoutes:
    """Tests for extracted online_store_routes.py"""
    
    def test_store_settings(self, tenant_token):
        """GET /api/store/settings (from extracted online_store_routes.py)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/store/settings", headers=headers)
        print(f"Store settings response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # Should have store settings fields
        assert "enabled" in data or isinstance(data, dict)
        print(f"Store settings: enabled={data.get('enabled')}")
    
    def test_woocommerce_settings(self, tenant_token):
        """GET /api/woocommerce/settings (from extracted online_store_routes.py)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/woocommerce/settings", headers=headers)
        print(f"WooCommerce settings response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print(f"WooCommerce settings: enabled={data.get('enabled')}")


class TestSMSMarketingRoutes:
    """Tests for extracted sms_marketing_routes.py"""
    
    def test_sms_settings(self, tenant_token):
        """GET /api/sms/settings (from extracted sms_marketing_routes.py)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/sms/settings", headers=headers)
        print(f"SMS settings response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should have SMS settings fields
        print(f"SMS settings: auto_reminder_enabled={data.get('auto_reminder_enabled')}")


class TestSendGridEmailRoutes:
    """Tests for extracted sendgrid_email_routes.py"""
    
    def test_email_settings(self, tenant_token):
        """GET /api/email/settings (from extracted sendgrid_email_routes.py)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/email/settings", headers=headers)
        print(f"Email settings response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print(f"Email settings: enabled={data.get('enabled')}")
    
    def test_sendgrid_settings(self, tenant_token):
        """GET /api/notifications/sendgrid/settings (from extracted sendgrid_email_routes.py)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications/sendgrid/settings", headers=headers)
        print(f"SendGrid settings response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print(f"SendGrid settings: enabled={data.get('enabled')}")


class TestStripeRoutes:
    """Tests for extracted stripe_routes.py"""
    
    def test_payment_packages(self):
        """GET /api/payments/packages (from extracted stripe_routes.py)"""
        response = requests.get(f"{BASE_URL}/api/payments/packages")
        print(f"Payment packages response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        # Should return list of subscription packages
        assert isinstance(data, list)
        if len(data) > 0:
            pkg = data[0]
            assert "id" in pkg
            assert "amount" in pkg
            print(f"Found {len(data)} payment packages")
        else:
            print("No payment packages configured")


class TestShippingAndLoyalty:
    """Test shipping companies and loyalty settings endpoints"""
    
    def test_shipping_companies(self, tenant_token):
        """GET /api/shipping/companies"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/shipping/companies", headers=headers)
        print(f"Shipping companies response: {response.status_code}")
        # Could be 200 or 404 if not configured
        assert response.status_code in [200, 404]
    
    def test_loyalty_settings(self, tenant_token):
        """GET /api/loyalty/settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/loyalty/settings", headers=headers)
        print(f"Loyalty settings response: {response.status_code}")
        # Could be 200 or 404 if not configured
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"Loyalty settings found: {data}")


class TestSaaSAdminRoutes:
    """Test SaaS admin endpoints (super admin only)"""
    
    def test_saas_tenants(self, super_admin_token):
        """GET /api/saas/tenants (super admin only)"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        print(f"SaaS tenants response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        # Could be paginated with 'tenants' key
        if isinstance(data, dict) and 'tenants' in data:
            print(f"Found {len(data['tenants'])} tenants")
        else:
            print(f"Found {len(data)} tenants")
    
    def test_saas_plans(self, super_admin_token):
        """GET /api/saas/plans (super admin only)"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/plans", headers=headers)
        print(f"SaaS plans response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        print(f"Found {len(data) if isinstance(data, list) else 'unknown'} plans")
    
    def test_robots_status(self, super_admin_token):
        """GET /api/robots/status (super admin only)"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/robots/status", headers=headers)
        print(f"Robots status response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        print(f"Robots data: {data}")


class TestCoreRoutes:
    """Test other core routes to ensure no regressions"""
    
    def test_customers(self, tenant_token):
        """GET /api/customers"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        print(f"Customers response: {response.status_code}")
        assert response.status_code == 200
    
    def test_sales(self, tenant_token):
        """GET /api/sales"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/sales", headers=headers)
        print(f"Sales response: {response.status_code}")
        assert response.status_code == 200
    
    def test_purchases(self, tenant_token):
        """GET /api/purchases"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/purchases", headers=headers)
        print(f"Purchases response: {response.status_code}")
        assert response.status_code == 200
    
    def test_cash_boxes(self, tenant_token):
        """GET /api/cash-boxes"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/cash-boxes", headers=headers)
        print(f"Cash boxes response: {response.status_code}")
        assert response.status_code == 200
    
    def test_expenses(self, tenant_token):
        """GET /api/expenses"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/expenses", headers=headers)
        print(f"Expenses response: {response.status_code}")
        assert response.status_code == 200
    
    def test_suppliers(self, tenant_token):
        """GET /api/suppliers"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=headers)
        print(f"Suppliers response: {response.status_code}")
        assert response.status_code == 200
    
    def test_warehouses(self, tenant_token):
        """GET /api/warehouses"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/warehouses", headers=headers)
        print(f"Warehouses response: {response.status_code}")
        assert response.status_code == 200
    
    def test_stats(self, tenant_token):
        """GET /api/stats"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/stats", headers=headers)
        print(f"Stats response: {response.status_code}")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
