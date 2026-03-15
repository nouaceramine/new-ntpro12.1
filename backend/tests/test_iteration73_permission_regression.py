"""
NT Commerce 12.0 - Iteration 73 Regression Tests
Tests:
1. Health and system info endpoints
2. Authentication (tenant login, super admin login, invalid login)
3. Permission-protected endpoints with authenticated admin user
4. Permission enforcement (reject unauthenticated requests)
5. Previously failing endpoints (SIM slots, invoice templates)
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://nt-commerce-refactor.preview.emergentagent.com"

# Test credentials
TENANT_EMAIL = "ncr@ntcommerce.com"
TENANT_PASSWORD = "Test@123"
SUPER_ADMIN_EMAIL = "admin@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "Admin@2024"


class TestHealthAndSystem:
    """Health and system info tests"""

    def test_health_endpoint(self):
        """GET /api/health - should return healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "healthy"
        print("PASS: Health endpoint returns healthy")

    def test_system_info(self):
        """GET /api/system/info - should return version 12.0.0 and 152 tables"""
        response = requests.get(f"{BASE_URL}/api/system/info")
        assert response.status_code == 200, f"System info failed: {response.text}"
        data = response.json()
        assert data.get("version") == "12.0.0", f"Unexpected version: {data.get('version')}"
        assert data.get("total_tables") == 152, f"Unexpected tables count: {data.get('total_tables')}"
        print(f"PASS: System info - v{data.get('version')}, {data.get('total_tables')} tables")


class TestAuthentication:
    """Authentication flow tests"""

    def test_tenant_login_success(self):
        """POST /api/auth/unified-login - tenant login should succeed"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        assert response.status_code == 200, f"Tenant login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user_type") == "tenant", f"Unexpected user_type: {data.get('user_type')}"
        print(f"PASS: Tenant login successful - user_type: {data.get('user_type')}")

    def test_super_admin_login_success(self):
        """POST /api/auth/unified-login - super admin login should succeed"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print(f"PASS: Super admin login successful")

    def test_invalid_login(self):
        """POST /api/auth/unified-login - invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Invalid login correctly rejected with 401")


@pytest.fixture(scope="class")
def tenant_token():
    """Get tenant authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
        "email": TENANT_EMAIL,
        "password": TENANT_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Tenant authentication failed")


@pytest.fixture(scope="class")
def super_admin_token():
    """Get super admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Super admin authentication failed")


class TestPermissionEnforcement:
    """Test that endpoints reject requests without authentication"""

    def test_products_requires_auth(self):
        """GET /api/products without auth should return 401/403"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}: {response.text}"
        print("PASS: /api/products correctly requires authentication")

    def test_sales_requires_auth(self):
        """GET /api/sales without auth should return 401/403"""
        response = requests.get(f"{BASE_URL}/api/sales")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: /api/sales correctly requires authentication")

    def test_customers_requires_auth(self):
        """GET /api/customers without auth should return 401/403"""
        response = requests.get(f"{BASE_URL}/api/customers")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: /api/customers correctly requires authentication")

    def test_invalid_token_rejected(self):
        """GET /api/products with invalid token should return 401"""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Invalid token correctly rejected")


class TestTenantEndpoints:
    """Test tenant-accessible endpoints with authentication"""

    @pytest.fixture(autouse=True)
    def setup(self, tenant_token):
        self.headers = {"Authorization": f"Bearer {tenant_token}"}

    # Products CRUD
    def test_get_products(self, tenant_token):
        """GET /api/products (permission: products.view)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200, f"Products GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Products should return a list"
        print(f"PASS: GET /api/products - returned {len(data)} products")

    # Sales list
    def test_get_sales(self, tenant_token):
        """GET /api/sales (permission: sales.view)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/sales", headers=headers)
        assert response.status_code == 200, f"Sales GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Sales should return a list"
        print(f"PASS: GET /api/sales - returned {len(data)} sales")

    # Customers list
    def test_get_customers(self, tenant_token):
        """GET /api/customers (permission: customers.view)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        assert response.status_code == 200, f"Customers GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Customers should return a list"
        print(f"PASS: GET /api/customers - returned {len(data)} customers")

    # Purchases list
    def test_get_purchases(self, tenant_token):
        """GET /api/purchases (permission: purchases.view)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/purchases", headers=headers)
        assert response.status_code == 200, f"Purchases GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Purchases should return a list"
        print(f"PASS: GET /api/purchases - returned {len(data)} purchases")

    # Expenses list
    def test_get_expenses(self, tenant_token):
        """GET /api/expenses (permission: expenses.view)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/expenses", headers=headers)
        assert response.status_code == 200, f"Expenses GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expenses should return a list"
        print(f"PASS: GET /api/expenses - returned {len(data)} expenses")

    # Employees list
    def test_get_employees(self, tenant_token):
        """GET /api/employees (permission: employees.view)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/employees", headers=headers)
        assert response.status_code == 200, f"Employees GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Employees should return a list"
        print(f"PASS: GET /api/employees - returned {len(data)} employees")

    # Warehouses list
    def test_get_warehouses(self, tenant_token):
        """GET /api/warehouses (permission: warehouses.view)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/warehouses", headers=headers)
        assert response.status_code == 200, f"Warehouses GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Warehouses should return a list"
        print(f"PASS: GET /api/warehouses - returned {len(data)} warehouses")

    # Debts list
    def test_get_debts(self, tenant_token):
        """GET /api/debts (permission: debts.view)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/debts", headers=headers)
        assert response.status_code == 200, f"Debts GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Debts should return a list"
        print(f"PASS: GET /api/debts - returned {len(data)} debts")

    # Daily sessions
    def test_get_daily_sessions(self, tenant_token):
        """GET /api/daily-sessions (permission: daily_sessions.view)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/daily-sessions", headers=headers)
        assert response.status_code == 200, f"Daily sessions GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Daily sessions should return a list"
        print(f"PASS: GET /api/daily-sessions - returned {len(data)} sessions")

    # Suppliers list
    def test_get_suppliers(self, tenant_token):
        """GET /api/suppliers (permission: suppliers.view)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=headers)
        assert response.status_code == 200, f"Suppliers GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Suppliers should return a list"
        print(f"PASS: GET /api/suppliers - returned {len(data)} suppliers")

    # Cash boxes
    def test_get_cash_boxes(self, tenant_token):
        """GET /api/cash-boxes (permission: cash_boxes.view)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/cash-boxes", headers=headers)
        assert response.status_code == 200, f"Cash boxes GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Cash boxes should return a list"
        print(f"PASS: GET /api/cash-boxes - returned {len(data)} cash boxes")


class TestSettingsAndConfig:
    """Test settings and configuration endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self, tenant_token):
        self.headers = {"Authorization": f"Bearer {tenant_token}"}

    def test_get_store_settings(self, tenant_token):
        """GET /api/store/settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/store/settings", headers=headers)
        assert response.status_code == 200, f"Store settings failed: {response.text}"
        print("PASS: GET /api/store/settings")

    def test_get_sms_settings(self, tenant_token):
        """GET /api/sms/settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/sms/settings", headers=headers)
        assert response.status_code == 200, f"SMS settings failed: {response.text}"
        print("PASS: GET /api/sms/settings")

    def test_get_email_settings(self, tenant_token):
        """GET /api/email/settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/email/settings", headers=headers)
        assert response.status_code == 200, f"Email settings failed: {response.text}"
        print("PASS: GET /api/email/settings")

    def test_get_payments_packages(self, tenant_token):
        """GET /api/payments/packages"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/payments/packages", headers=headers)
        assert response.status_code == 200, f"Payments packages failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Packages should return a list"
        print(f"PASS: GET /api/payments/packages - returned {len(data)} packages")

    def test_get_shipping_companies(self, tenant_token):
        """GET /api/shipping/companies"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/shipping/companies", headers=headers)
        assert response.status_code == 200, f"Shipping companies failed: {response.text}"
        print("PASS: GET /api/shipping/companies")

    def test_get_loyalty_settings(self, tenant_token):
        """GET /api/loyalty/settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/loyalty/settings", headers=headers)
        assert response.status_code == 200, f"Loyalty settings failed: {response.text}"
        print("PASS: GET /api/loyalty/settings")

    def test_get_invoice_templates(self, tenant_token):
        """GET /api/invoices/templates - FIXED in this iteration"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/invoices/templates", headers=headers)
        assert response.status_code == 200, f"Invoice templates failed: {response.text}"
        print("PASS: GET /api/invoices/templates (ObjectId fix verified)")

    def test_get_sim_slots(self, tenant_token):
        """GET /api/sim/slots - FIXED in this iteration"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/sim/slots", headers=headers)
        assert response.status_code == 200, f"SIM slots failed: {response.text}"
        print("PASS: GET /api/sim/slots (ObjectId fix verified)")

    def test_get_permissions_roles(self, tenant_token):
        """GET /api/permissions/roles"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/permissions/roles", headers=headers)
        assert response.status_code == 200, f"Permissions roles failed: {response.text}"
        print("PASS: GET /api/permissions/roles")


class TestSuperAdminEndpoints:
    """Test super admin only endpoints"""

    def test_get_saas_tenants(self, super_admin_token):
        """GET /api/saas/tenants (super admin only)"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        assert response.status_code == 200, f"SaaS tenants failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Tenants should return a list"
        print(f"PASS: GET /api/saas/tenants - returned {len(data)} tenants")

    def test_get_robots_status(self, super_admin_token):
        """GET /api/robots/status (super admin only)"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/robots/status", headers=headers)
        assert response.status_code == 200, f"Robots status failed: {response.text}"
        data = response.json()
        print(f"PASS: GET /api/robots/status - {len(data.get('robots', data))} robots")

    def test_get_system_updates_stats(self, super_admin_token):
        """GET /api/system-updates/stats (super admin only)"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/system-updates/stats", headers=headers)
        assert response.status_code == 200, f"System updates stats failed: {response.text}"
        print("PASS: GET /api/system-updates/stats")

    def test_tenant_cannot_access_saas_tenants(self, tenant_token):
        """Tenant should NOT be able to access super admin endpoints"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("PASS: Tenant correctly denied access to /api/saas/tenants")


class TestProductCRUD:
    """Test product create permission"""

    def test_product_create_with_auth(self, tenant_token):
        """POST /api/products (permission: products.create)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        test_product = {
            "name_ar": f"TEST_منتج اختبار {datetime.now().strftime('%H%M%S')}",
            "name_en": f"TEST_Test Product {datetime.now().strftime('%H%M%S')}",
            "purchase_price": 100,
            "wholesale_price": 120,
            "retail_price": 150,
            "quantity": 10,
            "low_stock_threshold": 5
        }
        response = requests.post(f"{BASE_URL}/api/products", json=test_product, headers=headers)
        assert response.status_code == 201, f"Product create failed: {response.text}"
        data = response.json()
        assert "id" in data, "No id in response"
        print(f"PASS: POST /api/products - created product {data.get('id')}")
        
        # Cleanup - delete the test product
        product_id = data.get("id")
        if product_id:
            requests.delete(f"{BASE_URL}/api/products/{product_id}", headers=headers)


class TestAuthMe:
    """Test auth/me endpoint"""

    def test_get_auth_me(self, tenant_token):
        """GET /api/auth/me - should return current user info"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        assert "email" in data or "id" in data, "No user info in response"
        print(f"PASS: GET /api/auth/me - user: {data.get('email', data.get('name', 'unknown'))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
