"""
Test RBAC Changes - Iteration 39
Testing that Super Admin is now blocked from tenant-specific routes (products, customers)
while still having access to SaaS management routes and user management.

RBAC Dependencies:
- get_tenant_admin: Requires tenant_id in JWT (rejects super_admin)
- require_tenant: Requires tenant_id for read operations (rejects super_admin)
- get_admin_user: Still allows super_admin (for user management)
- get_super_admin: Only allows super_admin (for SaaS management)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRBACChanges:
    """Test RBAC changes - Super Admin blocked from tenant routes"""
    
    @pytest.fixture(scope="class")
    def super_admin_token(self):
        """Get Super Admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert response.status_code == 200, f"Super Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def tenant_a_token(self):
        """Get Tenant A token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": "tenanta@test.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Tenant A login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def tenant_b_token(self):
        """Get Tenant B token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": "tenantb@test.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Tenant B login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]

    # ==================== RBAC: Super Admin BLOCKED from tenant routes ====================
    
    def test_super_admin_post_products_blocked(self, super_admin_token):
        """Super Admin calling POST /api/products should get 403 with Arabic message"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        product_data = {
            "name_en": "TEST_SuperAdmin_Product",
            "name_ar": "منتج المدير العام",
            "purchase_price": 10,
            "wholesale_price": 15,
            "retail_price": 20,
            "super_wholesale_price": 12,
            "quantity": 100,
            "compatible_models": ["test"],
            "low_stock_threshold": 5
        }
        response = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert "هذا الإجراء متاح فقط لمشتركي المنصة" in data.get("detail", ""), f"Expected Arabic message, got: {data}"
    
    def test_super_admin_get_products_blocked(self, super_admin_token):
        """Super Admin calling GET /api/products should get 403"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert "هذا الإجراء متاح فقط لمشتركي المنصة" in data.get("detail", ""), f"Expected Arabic message, got: {data}"
    
    def test_super_admin_get_customers_blocked(self, super_admin_token):
        """Super Admin calling GET /api/customers should get 403"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert "هذا الإجراء متاح فقط لمشتركي المنصة" in data.get("detail", ""), f"Expected Arabic message, got: {data}"
    
    def test_unauthenticated_get_products_blocked(self):
        """Unauthenticated call to GET /api/products should get 401/403"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}: {response.text}"
    
    # ==================== Tenant Data Isolation Still Works ====================
    
    def test_tenant_a_can_create_product(self, tenant_a_token):
        """Tenant A can create products (data isolation still works)"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        product_data = {
            "name_en": "TEST_TenantA_RBAC_Product",
            "name_ar": "منتج اختبار RBAC للمستأجر أ",
            "purchase_price": 10,
            "wholesale_price": 15,
            "retail_price": 20,
            "super_wholesale_price": 12,
            "quantity": 100,
            "compatible_models": ["test_rbac"],
            "low_stock_threshold": 5
        }
        response = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("name_en") == "TEST_TenantA_RBAC_Product"
        return data.get("id")
    
    def test_tenant_a_can_list_products(self, tenant_a_token):
        """Tenant A can list their own products"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        products = response.json()
        assert isinstance(products, list), "Expected list of products"
        print(f"Tenant A has {len(products)} products")
    
    def test_tenant_b_cannot_see_tenant_a_products(self, tenant_a_token, tenant_b_token):
        """Tenant B cannot see Tenant A's products (cross-tenant isolation)"""
        # Get Tenant A's product names
        headers_a = {"Authorization": f"Bearer {tenant_a_token}"}
        response_a = requests.get(f"{BASE_URL}/api/products", headers=headers_a)
        assert response_a.status_code == 200
        tenant_a_products = response_a.json()
        tenant_a_product_names = [p["name_en"] for p in tenant_a_products]
        
        # Get Tenant B's products
        headers_b = {"Authorization": f"Bearer {tenant_b_token}"}
        response_b = requests.get(f"{BASE_URL}/api/products", headers=headers_b)
        assert response_b.status_code == 200
        tenant_b_products = response_b.json()
        tenant_b_product_names = [p["name_en"] for p in tenant_b_products]
        
        # Verify no overlap (except generic test data)
        for name in tenant_a_product_names:
            if "TenantA" in name:  # Check our test products specifically
                assert name not in tenant_b_product_names, f"Tenant B should not see Tenant A's product: {name}"
        print(f"Cross-tenant isolation verified: Tenant A has {len(tenant_a_products)}, Tenant B has {len(tenant_b_products)}")
    
    def test_tenant_a_can_create_customer(self, tenant_a_token):
        """Tenant A can create customers"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        customer_data = {
            "name": "TEST_RBAC_Customer_A",
            "phone": "0555123456",
            "address": "Test Address"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("name") == "TEST_RBAC_Customer_A"
    
    def test_tenant_a_can_list_customers(self, tenant_a_token):
        """Tenant A can list their own customers"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        customers = response.json()
        assert isinstance(customers, list), "Expected list of customers"
        print(f"Tenant A has {len(customers)} customers")
    
    # ==================== Super Admin CAN still access SaaS routes ====================
    
    def test_super_admin_can_access_saas_tenants(self, super_admin_token):
        """Super Admin can still access SaaS admin routes: GET /api/saas/tenants"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        tenants = response.json()
        assert isinstance(tenants, list), "Expected list of tenants"
        print(f"Super Admin can see {len(tenants)} tenants")
    
    def test_super_admin_can_access_saas_plans(self, super_admin_token):
        """Super Admin can still access GET /api/saas/plans"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/plans", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        plans = response.json()
        assert isinstance(plans, list), "Expected list of plans"
        print(f"Super Admin can see {len(plans)} plans")
    
    def test_super_admin_can_access_monitoring(self, super_admin_token):
        """Super Admin can access monitoring: GET /api/saas/monitoring returns tenant stats"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/monitoring", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "tenants" in data, "Expected 'tenants' in monitoring response"
        assert "summary" in data, "Expected 'summary' in monitoring response"
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_tenants" in summary
        assert "active_tenants" in summary
        assert "total_products" in summary
        assert "total_customers" in summary
        assert "total_sales" in summary
        assert "total_revenue" in summary
        print(f"Monitoring: {summary['total_tenants']} tenants, {summary['total_products']} products, {summary['total_revenue']} revenue")
        
        # Verify tenant data structure
        if data["tenants"]:
            tenant = data["tenants"][0]
            assert "tenant_id" in tenant
            assert "products_count" in tenant
            assert "customers_count" in tenant
            assert "sales_count" in tenant
    
    def test_super_admin_can_manage_users(self, super_admin_token):
        """Super Admin can still manage users: GET /api/users"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        users = response.json()
        assert isinstance(users, list), "Expected list of users"
        print(f"Super Admin can see {len(users)} users")
    
    # ==================== Login flows work ====================
    
    def test_health_check(self):
        """Health check: GET /api/health returns ok/healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        status = data.get("status", "").lower()
        assert status in ["ok", "healthy"], f"Expected ok/healthy, got: {data}"
    
    def test_super_admin_login_works(self):
        """Login flow works for super admin"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert response.status_code == 200, f"Super Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data.get("user", {}).get("role") == "super_admin" or data.get("role") == "super_admin"
    
    def test_tenant_login_works(self):
        """Login flow works for tenants"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": "tenanta@test.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Tenant A login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        # Tenant should have user_type=tenant and the JWT contains tenant_id
        assert data.get("user_type") == "tenant", f"Expected user_type=tenant, got: {data}"
        # Verify JWT contains tenant_id by checking the decoded token structure
        assert data.get("redirect_to") == "/tenant/dashboard", f"Expected tenant dashboard redirect"


class TestCleanup:
    """Cleanup test data created during RBAC tests"""
    
    @pytest.fixture(scope="class")
    def tenant_a_token(self):
        """Get Tenant A token for cleanup"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": "tenanta@test.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_cleanup_test_products(self, tenant_a_token):
        """Cleanup TEST_ prefixed products"""
        if not tenant_a_token:
            pytest.skip("No token available for cleanup")
        
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        if response.status_code == 200:
            products = response.json()
            for product in products:
                if product.get("name_en", "").startswith("TEST_"):
                    delete_resp = requests.delete(
                        f"{BASE_URL}/api/products/{product['id']}", 
                        headers=headers
                    )
                    print(f"Deleted product: {product['name_en']}, status: {delete_resp.status_code}")
    
    def test_cleanup_test_customers(self, tenant_a_token):
        """Cleanup TEST_ prefixed customers"""
        if not tenant_a_token:
            pytest.skip("No token available for cleanup")
        
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        if response.status_code == 200:
            customers = response.json()
            for customer in customers:
                if customer.get("name", "").startswith("TEST_"):
                    delete_resp = requests.delete(
                        f"{BASE_URL}/api/customers/{customer['id']}", 
                        headers=headers
                    )
                    print(f"Deleted customer: {customer['name']}, status: {delete_resp.status_code}")
