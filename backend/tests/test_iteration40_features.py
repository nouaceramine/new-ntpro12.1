"""
Test iteration 40: New SaaS Features
1. Impersonation API - POST /api/saas/impersonate/{tenant_id}
2. Agent name column in tenant table - GET /api/saas/tenants returns agent_name
3. Monitoring alerts - GET /api/saas/monitoring returns alerts array
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


class TestImpersonationAPI:
    """Test impersonation endpoint POST /api/saas/impersonate/{tenant_id}"""
    
    def test_super_admin_can_get_tenant_list(self):
        """Super Admin can get list of tenants to get tenant_id"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None, "Super Admin login failed"
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        assert response.status_code == 200, f"Get tenants failed: {response.text}"
        
        tenants = response.json()
        assert isinstance(tenants, list), "Response should be a list"
        assert len(tenants) > 0, "Should have at least one tenant"
        
        # Store tenant_id for later tests
        first_tenant = tenants[0]
        assert "id" in first_tenant, "Tenant should have id field"
        print(f"✓ Found {len(tenants)} tenants")
        
    def test_impersonation_returns_valid_jwt(self):
        """Impersonation endpoint returns valid JWT token"""
        # Login as super admin
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None, "Super Admin login failed"
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        # Get tenant list first
        tenants_response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        tenants = tenants_response.json()
        assert len(tenants) > 0, "Need at least one tenant to test impersonation"
        
        # Get first active tenant
        active_tenant = next((t for t in tenants if t.get("is_active")), tenants[0])
        tenant_id = active_tenant["id"]
        
        # Call impersonation endpoint
        impersonate_response = requests.post(
            f"{BASE_URL}/api/saas/impersonate/{tenant_id}", 
            headers=headers
        )
        
        assert impersonate_response.status_code == 200, f"Impersonation failed: {impersonate_response.text}"
        
        data = impersonate_response.json()
        assert "access_token" in data, "Should return access_token"
        assert data.get("token_type") == "bearer", "Token type should be bearer"
        assert data.get("tenant_id") == tenant_id, "Should return correct tenant_id"
        assert "email" in data, "Should return tenant email"
        
        print(f"✓ Impersonation successful for tenant: {data.get('email')}")
        
    def test_impersonation_token_can_list_tenant_products(self):
        """Token from impersonation can list products for that tenant only"""
        # Login as super admin
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        # Get tenants
        tenants_response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        tenants = tenants_response.json()
        active_tenant = next((t for t in tenants if t.get("is_active")), tenants[0])
        tenant_id = active_tenant["id"]
        
        # Impersonate tenant
        impersonate_response = requests.post(
            f"{BASE_URL}/api/saas/impersonate/{tenant_id}", 
            headers=headers
        )
        assert impersonate_response.status_code == 200
        
        impersonation_token = impersonate_response.json().get("access_token")
        impersonation_headers = TestHelpers.get_auth_header(impersonation_token)
        
        # Use impersonation token to get products
        products_response = requests.get(
            f"{BASE_URL}/api/products", 
            headers=impersonation_headers
        )
        
        # Should be able to access products with impersonated token
        assert products_response.status_code == 200, f"Failed to get products with impersonation token: {products_response.text}"
        
        products = products_response.json()
        assert isinstance(products, (list, dict)), "Products response should be list or dict"
        print(f"✓ Impersonation token can access tenant products")
        
    def test_impersonation_preserves_data_isolation(self):
        """Impersonation token for Tenant A cannot see Tenant B's data"""
        # Login as super admin
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        # Get tenants - find two different active tenants
        tenants_response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        tenants = tenants_response.json()
        
        active_tenants = [t for t in tenants if t.get("is_active")]
        
        if len(active_tenants) < 2:
            pytest.skip("Need at least 2 active tenants to test data isolation")
        
        tenant_a_id = active_tenants[0]["id"]
        tenant_b_id = active_tenants[1]["id"]
        
        # Impersonate Tenant A
        impersonate_a_response = requests.post(
            f"{BASE_URL}/api/saas/impersonate/{tenant_a_id}", 
            headers=headers
        )
        assert impersonate_a_response.status_code == 200
        token_a = impersonate_a_response.json().get("access_token")
        
        # Impersonate Tenant B
        impersonate_b_response = requests.post(
            f"{BASE_URL}/api/saas/impersonate/{tenant_b_id}", 
            headers=headers
        )
        assert impersonate_b_response.status_code == 200
        token_b = impersonate_b_response.json().get("access_token")
        
        # Create a test product using Tenant A's impersonation token
        test_product = {
            "name": "TEST_IMPERSONATION_PRODUCT_A",
            "barcode": "TEST_IMP_A_001",
            "price": 100.0,
            "quantity": 10,
            "category": "Test"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/products",
            headers=TestHelpers.get_auth_header(token_a),
            json=test_product
        )
        
        # Get products as Tenant A (impersonated)
        products_a_response = requests.get(
            f"{BASE_URL}/api/products",
            headers=TestHelpers.get_auth_header(token_a)
        )
        products_a = products_a_response.json()
        
        # Get products as Tenant B (impersonated)
        products_b_response = requests.get(
            f"{BASE_URL}/api/products",
            headers=TestHelpers.get_auth_header(token_b)
        )
        products_b = products_b_response.json()
        
        # Handle both list and paginated responses
        products_a_list = products_a if isinstance(products_a, list) else products_a.get("items", [])
        products_b_list = products_b if isinstance(products_b, list) else products_b.get("items", [])
        
        # Tenant B should NOT see Tenant A's test product
        test_product_in_b = any(p.get("name") == "TEST_IMPERSONATION_PRODUCT_A" for p in products_b_list)
        assert not test_product_in_b, "Data isolation violated: Tenant B can see Tenant A's product!"
        
        print(f"✓ Data isolation preserved between impersonated tenants")
        
        # Cleanup - delete test product
        if create_response.status_code in [200, 201]:
            created_product = create_response.json()
            product_id = created_product.get("id")
            if product_id:
                requests.delete(
                    f"{BASE_URL}/api/products/{product_id}",
                    headers=TestHelpers.get_auth_header(token_a)
                )
        
    def test_non_super_admin_cannot_impersonate(self):
        """Non-super-admin users cannot call impersonation endpoint (403)"""
        # Login as regular tenant
        login_data = TestHelpers.login(TENANT_A_EMAIL, TENANT_A_PASSWORD)
        assert login_data is not None, "Tenant A login failed"
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        # Try to impersonate (should fail with 403)
        # Use a random tenant_id since we shouldn't have access anyway
        impersonate_response = requests.post(
            f"{BASE_URL}/api/saas/impersonate/some-tenant-id", 
            headers=headers
        )
        
        assert impersonate_response.status_code == 403, \
            f"Expected 403 for non-super-admin, got {impersonate_response.status_code}: {impersonate_response.text}"
        
        print(f"✓ Non-super-admin correctly blocked from impersonation (403)")
        
    def test_impersonate_nonexistent_tenant_returns_404(self):
        """Impersonating non-existent tenant returns 404"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.post(
            f"{BASE_URL}/api/saas/impersonate/nonexistent-tenant-id-12345", 
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent tenant returns 404")


class TestAgentNameInTenants:
    """Test agent_name field in GET /api/saas/tenants"""
    
    def test_tenants_response_includes_agent_name_field(self):
        """GET /api/saas/tenants returns agent_name field"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        assert response.status_code == 200
        
        tenants = response.json()
        assert len(tenants) > 0, "Should have at least one tenant"
        
        # Check that agent_name field exists in tenant response
        first_tenant = tenants[0]
        assert "agent_name" in first_tenant, "Tenant should have agent_name field"
        
        # agent_name can be empty string if no agent assigned
        agent_name = first_tenant.get("agent_name")
        assert isinstance(agent_name, str), "agent_name should be a string"
        
        # Check all tenants have agent_name field
        all_have_agent_name = all("agent_name" in t for t in tenants)
        assert all_have_agent_name, "All tenants should have agent_name field"
        
        # Log tenants with agents
        tenants_with_agents = [t for t in tenants if t.get("agent_name")]
        print(f"✓ agent_name field present in all {len(tenants)} tenants")
        print(f"  {len(tenants_with_agents)} tenants have assigned agents")


class TestMonitoringAlerts:
    """Test monitoring alerts in GET /api/saas/monitoring"""
    
    def test_monitoring_returns_alerts_array(self):
        """GET /api/saas/monitoring returns alerts array"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/monitoring", headers=headers)
        assert response.status_code == 200, f"Monitoring endpoint failed: {response.text}"
        
        data = response.json()
        
        # Check response structure
        assert "alerts" in data, "Response should include alerts array"
        assert isinstance(data["alerts"], list), "alerts should be a list"
        
        # Also check other expected fields
        assert "tenants" in data, "Response should include tenants data"
        assert "summary" in data, "Response should include summary"
        
        print(f"✓ Monitoring returns alerts array with {len(data['alerts'])} alerts")
        
    def test_monitoring_alert_structure(self):
        """Each alert has correct structure (type, severity, message, tenant_name)"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/monitoring", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        alerts = data.get("alerts", [])
        
        if len(alerts) == 0:
            pytest.skip("No alerts to verify structure - need tenants with expiring/expired subscriptions")
        
        for alert in alerts:
            assert "type" in alert, "Alert should have type"
            assert "severity" in alert, "Alert should have severity"
            assert "message" in alert, "Alert should have message"
            assert "tenant_name" in alert, "Alert should have tenant_name"
            assert "tenant_id" in alert, "Alert should have tenant_id"
            
            # Validate severity is one of expected values
            valid_severities = ["critical", "warning", "info"]
            assert alert["severity"] in valid_severities, f"Invalid severity: {alert['severity']}"
            
            # Validate alert types
            valid_types = ["expiring_soon", "expired", "product_limit", "user_limit"]
            assert alert["type"] in valid_types, f"Invalid alert type: {alert['type']}"
        
        print(f"✓ All {len(alerts)} alerts have correct structure")
        
    def test_expired_subscription_has_critical_severity(self):
        """Expired subscriptions should have 'critical' severity"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/monitoring", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        alerts = data.get("alerts", [])
        
        # Find expired alerts
        expired_alerts = [a for a in alerts if a.get("type") == "expired"]
        
        if len(expired_alerts) == 0:
            # Check tenants for amir@amir (mentioned as having expired subscription)
            print("ℹ No expired subscription alerts found - checking for expected tenant")
            pytest.skip("No expired subscription alerts found (amir@amir should have expired subscription)")
        
        for alert in expired_alerts:
            assert alert["severity"] == "critical", \
                f"Expired subscription should have critical severity, got {alert['severity']}"
            assert alert.get("days_left", 1) <= 0, "Expired should have days_left <= 0"
        
        print(f"✓ {len(expired_alerts)} expired subscription alerts have critical severity")
        
    def test_expiring_soon_has_warning_severity(self):
        """Expiring subscriptions (1-7 days) should have 'warning' severity"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/monitoring", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        alerts = data.get("alerts", [])
        
        # Find expiring soon alerts
        expiring_alerts = [a for a in alerts if a.get("type") == "expiring_soon"]
        
        if len(expiring_alerts) == 0:
            # Check tenants for farid@farid (mentioned as expiring in 3 days)
            print("ℹ No expiring subscription alerts found - checking for expected tenant")
            pytest.skip("No expiring subscription alerts found (farid@farid should be expiring in 3 days)")
        
        for alert in expiring_alerts:
            assert alert["severity"] == "warning", \
                f"Expiring subscription should have warning severity, got {alert['severity']}"
            days_left = alert.get("days_left", 0)
            assert 0 < days_left <= 7, f"Expiring alert should have 1-7 days left, got {days_left}"
        
        print(f"✓ {len(expiring_alerts)} expiring subscription alerts have warning severity")
        
    def test_alerts_sorted_by_severity(self):
        """Alerts should be sorted: critical first, then warning, then info"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/saas/monitoring", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        alerts = data.get("alerts", [])
        
        if len(alerts) < 2:
            pytest.skip("Need at least 2 alerts to verify sorting")
        
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        
        for i in range(len(alerts) - 1):
            current_order = severity_order.get(alerts[i]["severity"], 3)
            next_order = severity_order.get(alerts[i + 1]["severity"], 3)
            assert current_order <= next_order, \
                f"Alerts not sorted correctly: {alerts[i]['severity']} should come before {alerts[i + 1]['severity']}"
        
        print(f"✓ Alerts correctly sorted by severity")


class TestDataIsolationStillWorks:
    """Verify data isolation between tenants still works"""
    
    def test_tenant_a_cannot_see_tenant_b_products(self):
        """Tenant A products not visible to Tenant B"""
        # Login as Tenant A
        login_a = TestHelpers.login(TENANT_A_EMAIL, TENANT_A_PASSWORD)
        assert login_a is not None, "Tenant A login failed"
        token_a = login_a.get("access_token")
        
        # Login as Tenant B
        login_b = TestHelpers.login(TENANT_B_EMAIL, TENANT_B_PASSWORD)
        assert login_b is not None, "Tenant B login failed"
        token_b = login_b.get("access_token")
        
        # Create test product as Tenant A
        test_product = {
            "name": "TEST_ISOLATION_PRODUCT_A",
            "barcode": "TEST_ISO_A_001",
            "price": 50.0,
            "quantity": 5,
            "category": "Test"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/products",
            headers=TestHelpers.get_auth_header(token_a),
            json=test_product
        )
        
        # Get Tenant B's products
        products_b_response = requests.get(
            f"{BASE_URL}/api/products",
            headers=TestHelpers.get_auth_header(token_b)
        )
        
        if products_b_response.status_code != 200:
            pytest.skip("Could not get products as Tenant B")
        
        products_b = products_b_response.json()
        products_b_list = products_b if isinstance(products_b, list) else products_b.get("items", [])
        
        # Tenant B should NOT see Tenant A's test product
        test_product_in_b = any(p.get("name") == "TEST_ISOLATION_PRODUCT_A" for p in products_b_list)
        assert not test_product_in_b, "Data isolation violated: Tenant B sees Tenant A's product!"
        
        print(f"✓ Data isolation working: Tenant B cannot see Tenant A's products")
        
        # Cleanup
        if create_response.status_code in [200, 201]:
            created_product = create_response.json()
            product_id = created_product.get("id")
            if product_id:
                requests.delete(
                    f"{BASE_URL}/api/products/{product_id}",
                    headers=TestHelpers.get_auth_header(token_a)
                )


class TestRBACStillWorks:
    """Verify RBAC still works: Super Admin cannot access tenant-specific routes"""
    
    def test_super_admin_blocked_from_products(self):
        """Super Admin cannot access GET /api/products (should get 403)"""
        login_data = TestHelpers.login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD)
        assert login_data is not None
        
        token = login_data.get("access_token")
        headers = TestHelpers.get_auth_header(token)
        
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        
        assert response.status_code == 403, \
            f"Expected 403 for Super Admin on /api/products, got {response.status_code}"
        
        print(f"✓ Super Admin correctly blocked from GET /api/products (403)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
