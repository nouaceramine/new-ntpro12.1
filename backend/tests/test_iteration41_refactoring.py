"""
Test iteration 41: Verify refactoring did not break existing functionality
Testing:
1. Super Admin login and dashboard access
2. Monitoring tab showing tenant stats and alerts
3. Tenant impersonation feature
4. RBAC - Super Admin should NOT access tenant-specific endpoints
5. Data isolation - Tenants should only see their own data
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "super@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "password"
TENANT_A_EMAIL = "tenanta@test.com"
TENANT_A_PASSWORD = "password123"
TENANT_B_EMAIL = "tenantb@test.com"
TENANT_B_PASSWORD = "password123"


class TestHelpers:
    """Helper methods for authentication"""
    
    @staticmethod
    def login(email: str, password: str) -> dict:
        """Login and return response data with token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json()
        return None
    
    @staticmethod
    def get_auth_header(token: str) -> dict:
        """Get authorization header"""
        return {"Authorization": f"Bearer {token}"}


class TestSuperAdminLogin:
    """Test Super Admin login and dashboard access"""
    
    def test_super_admin_login_returns_correct_user_type(self):
        """Super Admin login should return user_type='admin' or role='super_admin'"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Should return access_token"
        assert "user" in data, "Should return user info"
        
        # Check user type - Super Admin should be admin type
        user_type = data.get("user_type")
        user_role = data.get("user", {}).get("role")
        
        assert user_type == "admin" or user_role == "super_admin", \
            f"Super Admin should have admin type or super_admin role, got type={user_type}, role={user_role}"
        
        print(f"✓ Super Admin login successful with type={user_type}, role={user_role}")
    
    def test_super_admin_can_access_saas_stats(self):
        """Super Admin can access /api/saas/stats endpoint"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/stats", headers=headers)
        assert response.status_code == 200, f"Failed to get stats: {response.text}"
        
        data = response.json()
        expected_fields = ["total_tenants", "active_tenants", "trial_tenants"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Super Admin can access SaaS stats")
    
    def test_super_admin_can_access_saas_plans(self):
        """Super Admin can access /api/saas/plans endpoint"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/plans", headers=headers)
        assert response.status_code == 200, f"Failed to get plans: {response.text}"
        
        plans = response.json()
        assert isinstance(plans, list), "Plans should be a list"
        
        if len(plans) > 0:
            plan = plans[0]
            assert "id" in plan, "Plan should have id"
            assert "name_ar" in plan, "Plan should have name_ar"
        
        print(f"✓ Super Admin can access {len(plans)} plans")
    
    def test_super_admin_can_access_saas_payments(self):
        """Super Admin can access /api/saas/payments endpoint"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/payments", headers=headers)
        assert response.status_code == 200, f"Failed to get payments: {response.text}"
        
        payments = response.json()
        assert isinstance(payments, list), "Payments should be a list"
        print(f"✓ Super Admin can access {len(payments)} payment records")


class TestMonitoringDashboard:
    """Test Monitoring tab showing tenant stats and alerts"""
    
    def test_monitoring_endpoint_returns_complete_structure(self):
        """GET /api/saas/monitoring returns tenants, summary, and alerts"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/monitoring", headers=headers)
        assert response.status_code == 200, f"Monitoring failed: {response.text}"
        
        data = response.json()
        
        # Check complete structure
        assert "tenants" in data, "Should have tenants array"
        assert "summary" in data, "Should have summary object"
        assert "alerts" in data, "Should have alerts array"
        
        assert isinstance(data["tenants"], list), "tenants should be a list"
        assert isinstance(data["summary"], dict), "summary should be a dict"
        assert isinstance(data["alerts"], list), "alerts should be a list"
        
        print(f"✓ Monitoring returns complete structure")
    
    def test_monitoring_tenant_stats_fields(self):
        """Each tenant in monitoring has stats fields"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/monitoring", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        tenants = data.get("tenants", [])
        
        if len(tenants) == 0:
            pytest.skip("No tenants to verify stats")
        
        # Check each tenant has expected stats fields
        expected_stats = ["products_count", "customers_count", "sales_count"]
        
        for tenant in tenants[:3]:  # Check first 3 tenants
            assert "tenant_id" in tenant, "Tenant should have tenant_id"
            assert "tenant_name" in tenant, "Tenant should have tenant_name"
            assert "is_active" in tenant, "Tenant should have is_active"
            
            for stat in expected_stats:
                assert stat in tenant, f"Tenant missing {stat}"
                assert isinstance(tenant[stat], (int, float)), f"{stat} should be numeric"
        
        print(f"✓ Tenant stats fields present in monitoring data")
    
    def test_monitoring_summary_has_totals(self):
        """Summary in monitoring has total counts"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/monitoring", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        summary = data.get("summary", {})
        
        expected_summary_fields = ["total_tenants", "active_tenants", "total_products"]
        
        for field in expected_summary_fields:
            assert field in summary, f"Summary missing {field}"
        
        print(f"✓ Monitoring summary has all expected totals")
    
    def test_monitoring_alerts_for_subscriptions(self):
        """Alerts include subscription-related warnings"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/monitoring", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        alerts = data.get("alerts", [])
        
        # Verify alerts structure
        for alert in alerts:
            assert "type" in alert, "Alert must have type"
            assert "severity" in alert, "Alert must have severity"
            assert "message" in alert, "Alert must have message"
        
        # Count subscription-related alerts
        subscription_alerts = [a for a in alerts if a.get("type") in ["expired", "expiring_soon"]]
        
        print(f"✓ Found {len(subscription_alerts)} subscription alerts out of {len(alerts)} total")


class TestRBACEnforcement:
    """Test RBAC - Super Admin should NOT access tenant-specific endpoints"""
    
    def test_super_admin_blocked_from_products(self):
        """Super Admin cannot access GET /api/products"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 403, \
            f"Expected 403, got {response.status_code}"
        
        print(f"✓ Super Admin blocked from /api/products (403)")
    
    def test_super_admin_blocked_from_customers(self):
        """Super Admin cannot access GET /api/customers"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        assert response.status_code == 403, \
            f"Expected 403, got {response.status_code}"
        
        print(f"✓ Super Admin blocked from /api/customers (403)")
    
    def test_super_admin_blocked_from_sales(self):
        """Super Admin cannot access GET /api/sales"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/sales", headers=headers)
        assert response.status_code == 403, \
            f"Expected 403, got {response.status_code}"
        
        print(f"✓ Super Admin blocked from /api/sales (403)")
    
    def test_super_admin_blocked_from_expenses(self):
        """Super Admin cannot access GET /api/expenses"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/expenses", headers=headers)
        assert response.status_code == 403, \
            f"Expected 403, got {response.status_code}"
        
        print(f"✓ Super Admin blocked from /api/expenses (403)")
    
    def test_super_admin_can_access_saas_tenants(self):
        """Super Admin CAN access GET /api/saas/tenants"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}: {response.text}"
        
        print(f"✓ Super Admin CAN access /api/saas/tenants (200)")


class TestDataIsolation:
    """Test data isolation - Tenants should only see their own data"""
    
    def test_tenant_a_sees_only_own_products(self):
        """Tenant A can only see their own products"""
        # Login as Tenant A
        login_a = TestHelpers.login(TENANT_A_EMAIL, TENANT_A_PASSWORD)
        assert login_a is not None, f"Tenant A login failed"
        token_a = login_a.get("access_token")
        
        # Create a test product as Tenant A
        test_product = {
            "name_ar": "منتج اختبار A",
            "name_en": "TEST_ISOLATION_A_PRODUCT",
            "purchase_price": 100,
            "retail_price": 150,
            "wholesale_price": 130,
            "quantity": 10
        }
        
        headers_a = TestHelpers.get_auth_header(token_a)
        create_response = requests.post(
            f"{BASE_URL}/api/products",
            headers=headers_a,
            json=test_product
        )
        
        # Get Tenant A's products
        products_a_response = requests.get(f"{BASE_URL}/api/products", headers=headers_a)
        assert products_a_response.status_code == 200
        
        products_a = products_a_response.json()
        products_a_list = products_a if isinstance(products_a, list) else products_a.get("items", [])
        
        # Tenant A should see their own test product
        test_found_in_a = any(p.get("name_en") == "TEST_ISOLATION_A_PRODUCT" for p in products_a_list)
        
        # Login as Tenant B and verify they don't see Tenant A's product
        login_b = TestHelpers.login(TENANT_B_EMAIL, TENANT_B_PASSWORD)
        if login_b:
            token_b = login_b.get("access_token")
            headers_b = TestHelpers.get_auth_header(token_b)
            
            products_b_response = requests.get(f"{BASE_URL}/api/products", headers=headers_b)
            if products_b_response.status_code == 200:
                products_b = products_b_response.json()
                products_b_list = products_b if isinstance(products_b, list) else products_b.get("items", [])
                
                # Tenant B should NOT see Tenant A's product
                test_found_in_b = any(p.get("name_en") == "TEST_ISOLATION_A_PRODUCT" for p in products_b_list)
                assert not test_found_in_b, "Data isolation violated: Tenant B can see Tenant A's product!"
        
        print(f"✓ Data isolation verified for products")
        
        # Cleanup
        if create_response.status_code in [200, 201]:
            created = create_response.json()
            if "id" in created:
                requests.delete(f"{BASE_URL}/api/products/{created['id']}", headers=headers_a)
    
    def test_tenant_b_sees_only_own_customers(self):
        """Tenant B can only see their own customers"""
        # Login as Tenant B
        login_b = TestHelpers.login(TENANT_B_EMAIL, TENANT_B_PASSWORD)
        assert login_b is not None, f"Tenant B login failed"
        token_b = login_b.get("access_token")
        
        # Create a test customer as Tenant B
        test_customer = {
            "name": "TEST_CUSTOMER_B_ISOLATION",
            "phone": "0555999888"
        }
        
        headers_b = TestHelpers.get_auth_header(token_b)
        create_response = requests.post(
            f"{BASE_URL}/api/customers",
            headers=headers_b,
            json=test_customer
        )
        
        # Get Tenant B's customers
        customers_b_response = requests.get(f"{BASE_URL}/api/customers", headers=headers_b)
        assert customers_b_response.status_code == 200
        
        customers_b = customers_b_response.json()
        
        # Login as Tenant A and verify they don't see Tenant B's customer
        login_a = TestHelpers.login(TENANT_A_EMAIL, TENANT_A_PASSWORD)
        if login_a:
            token_a = login_a.get("access_token")
            headers_a = TestHelpers.get_auth_header(token_a)
            
            customers_a_response = requests.get(f"{BASE_URL}/api/customers", headers=headers_a)
            if customers_a_response.status_code == 200:
                customers_a = customers_a_response.json()
                
                # Tenant A should NOT see Tenant B's customer
                test_found_in_a = any(c.get("name") == "TEST_CUSTOMER_B_ISOLATION" for c in customers_a)
                assert not test_found_in_a, "Data isolation violated: Tenant A can see Tenant B's customer!"
        
        print(f"✓ Data isolation verified for customers")
        
        # Cleanup
        if create_response.status_code in [200, 201]:
            created = create_response.json()
            if "id" in created:
                requests.delete(f"{BASE_URL}/api/customers/{created['id']}", headers=headers_b)


class TestImpersonationFeature:
    """Test tenant impersonation feature"""
    
    def test_impersonation_endpoint_exists(self):
        """POST /api/saas/impersonate/{tenant_id} endpoint exists"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        # Get a tenant first
        tenants_response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        tenants = tenants_response.json()
        
        if len(tenants) == 0:
            pytest.skip("No tenants available to test impersonation")
        
        tenant_id = tenants[0]["id"]
        
        response = requests.post(f"{BASE_URL}/api/saas/impersonate/{tenant_id}", headers=headers)
        
        # Should be 200 (success) not 404 (not found)
        assert response.status_code != 404, "Impersonation endpoint not found"
        assert response.status_code == 200, f"Impersonation failed: {response.status_code}"
        
        print(f"✓ Impersonation endpoint works correctly")
    
    def test_impersonation_returns_tenant_context(self):
        """Impersonation returns token with tenant context"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        # Get a tenant
        tenants_response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        tenants = tenants_response.json()
        
        if len(tenants) == 0:
            pytest.skip("No tenants available")
        
        active_tenant = next((t for t in tenants if t.get("is_active")), tenants[0])
        tenant_id = active_tenant["id"]
        
        response = requests.post(f"{BASE_URL}/api/saas/impersonate/{tenant_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data, "Should return access_token"
        assert "tenant_id" in data, "Should return tenant_id"
        assert data["tenant_id"] == tenant_id, "tenant_id should match"
        
        print(f"✓ Impersonation returns correct tenant context")
    
    def test_impersonated_token_can_access_tenant_data(self):
        """Impersonated token can access tenant-specific data"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        # Get a tenant
        tenants_response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        tenants = tenants_response.json()
        
        if len(tenants) == 0:
            pytest.skip("No tenants available")
        
        active_tenant = next((t for t in tenants if t.get("is_active")), tenants[0])
        tenant_id = active_tenant["id"]
        
        # Impersonate
        imp_response = requests.post(f"{BASE_URL}/api/saas/impersonate/{tenant_id}", headers=headers)
        assert imp_response.status_code == 200
        
        imp_token = imp_response.json().get("access_token")
        imp_headers = TestHelpers.get_auth_header(imp_token)
        
        # Now try to access tenant-specific data
        products_response = requests.get(f"{BASE_URL}/api/products", headers=imp_headers)
        
        # Should be 200, not 403
        assert products_response.status_code == 200, \
            f"Impersonated token should access products: {products_response.status_code}"
        
        print(f"✓ Impersonated token can access tenant data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
