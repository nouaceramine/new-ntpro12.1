"""
Comprehensive tests for Intelligent Robots feature
Testing all robot endpoints including status, run, restart, and lifecycle
Also verifying auth requirements and integration with auth endpoints
"""
import pytest
import httpx

API_URL = "https://ai-accounting-saas.preview.emergentagent.com"

# ============ CREDENTIALS ============
SUPER_ADMIN_EMAIL = "admin@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "Admin@2024"
TENANT_EMAIL = "ncr@ntcommerce.com"
TENANT_PASSWORD = "Test@123"


# ============ FIXTURES ============
@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin token for robot management"""
    resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
        "email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD
    })
    assert resp.status_code == 200, f"Super admin login failed: {resp.text}"
    data = resp.json()
    assert "access_token" in data
    assert data["user_type"] == "admin"
    return data["access_token"]


@pytest.fixture(scope="module")
def tenant_token():
    """Get tenant token for regular user operations"""
    resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
        "email": TENANT_EMAIL, "password": TENANT_PASSWORD
    })
    assert resp.status_code == 200, f"Tenant login failed: {resp.text}"
    data = resp.json()
    assert "access_token" in data
    return data["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ============ AUTH TESTS ============
class TestAuthEndpoints:
    """Verify authentication still works correctly"""
    
    def test_super_admin_login_success(self):
        """Test super admin login with correct credentials"""
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user_type"] == "admin"
        assert data["redirect_to"] == "/saas-admin"
        assert data["user"]["email"] == SUPER_ADMIN_EMAIL

    def test_tenant_login_success(self):
        """Test tenant login with correct credentials"""
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL, "password": TENANT_PASSWORD
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == TENANT_EMAIL

    def test_invalid_login_rejected(self):
        """Test that invalid credentials are rejected"""
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": "invalid@email.com", "password": "wrongpassword"
        })
        assert resp.status_code in [401, 404]


# ============ ROBOT STATUS TESTS ============
class TestRobotStatus:
    """Test GET /api/robots/status endpoint"""
    
    def test_get_status_with_auth(self, super_admin_token):
        """GET /api/robots/status - returns all 3 robots status"""
        resp = httpx.get(f"{API_URL}/api/robots/status", headers=auth_headers(super_admin_token))
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify structure
        assert "is_running" in data
        assert "robots" in data
        
        # Verify all 3 robots are present
        robots = data["robots"]
        assert "inventory" in robots, "Inventory robot missing"
        assert "debt" in robots, "Debt robot missing"
        assert "report" in robots, "Report robot missing"
        
        # Verify each robot has required fields
        for robot_name in ["inventory", "debt", "report"]:
            robot = robots[robot_name]
            assert "name" in robot, f"{robot_name} missing 'name'"
            assert "is_running" in robot, f"{robot_name} missing 'is_running'"
            assert "stats" in robot, f"{robot_name} missing 'stats'"
            assert "last_run" in robot, f"{robot_name} missing 'last_run'"
    
    def test_status_without_auth_rejected(self):
        """GET /api/robots/status without token returns 401/403"""
        resp = httpx.get(f"{API_URL}/api/robots/status")
        assert resp.status_code in [401, 403]
    
    def test_status_with_tenant_token_rejected(self, tenant_token):
        """GET /api/robots/status with tenant token returns 403 (super_admin required)"""
        resp = httpx.get(f"{API_URL}/api/robots/status", headers=auth_headers(tenant_token))
        assert resp.status_code == 403


# ============ ROBOT RUN TESTS ============
class TestRobotRun:
    """Test POST /api/robots/run/{robot_name} endpoints"""
    
    def test_run_inventory_robot(self, super_admin_token):
        """POST /api/robots/run/inventory - triggers inventory check"""
        resp = httpx.post(
            f"{API_URL}/api/robots/run/inventory", 
            headers=auth_headers(super_admin_token),
            timeout=30.0  # Allow longer timeout for robot execution
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "stats" in data
        assert data["stats"]["checks"] >= 1, "Inventory robot should have done at least 1 check"
    
    def test_run_debt_robot(self, super_admin_token):
        """POST /api/robots/run/debt - triggers debt collection check"""
        resp = httpx.post(
            f"{API_URL}/api/robots/run/debt", 
            headers=auth_headers(super_admin_token),
            timeout=30.0
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "stats" in data
        assert "checks" in data["stats"]
    
    def test_run_report_robot(self, super_admin_token):
        """POST /api/robots/run/report - generates daily report"""
        resp = httpx.post(
            f"{API_URL}/api/robots/run/report", 
            headers=auth_headers(super_admin_token),
            timeout=30.0
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "stats" in data
        assert "checks" in data["stats"]
    
    def test_run_nonexistent_robot(self, super_admin_token):
        """POST /api/robots/run/nonexistent - returns 404"""
        resp = httpx.post(
            f"{API_URL}/api/robots/run/nonexistent", 
            headers=auth_headers(super_admin_token)
        )
        assert resp.status_code == 404


# ============ ROBOT RESTART TESTS ============
class TestRobotRestart:
    """Test POST /api/robots/restart/{robot_name} endpoints"""
    
    def test_restart_inventory_robot(self, super_admin_token):
        """POST /api/robots/restart/inventory - restarts inventory robot"""
        resp = httpx.post(
            f"{API_URL}/api/robots/restart/inventory", 
            headers=auth_headers(super_admin_token),
            timeout=10.0
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
    
    def test_restart_debt_robot(self, super_admin_token):
        """POST /api/robots/restart/debt - restarts debt robot"""
        resp = httpx.post(
            f"{API_URL}/api/robots/restart/debt", 
            headers=auth_headers(super_admin_token),
            timeout=10.0
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
    
    def test_restart_report_robot(self, super_admin_token):
        """POST /api/robots/restart/report - restarts report robot"""
        resp = httpx.post(
            f"{API_URL}/api/robots/restart/report", 
            headers=auth_headers(super_admin_token),
            timeout=10.0
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
    
    def test_restart_nonexistent_robot(self, super_admin_token):
        """POST /api/robots/restart/nonexistent - returns 404"""
        resp = httpx.post(
            f"{API_URL}/api/robots/restart/nonexistent", 
            headers=auth_headers(super_admin_token)
        )
        assert resp.status_code == 404


# ============ ROBOT LIFECYCLE TESTS ============
class TestRobotLifecycle:
    """Test robot stop-all and start-all endpoints"""
    
    def test_stop_all_robots(self, super_admin_token):
        """POST /api/robots/stop-all - stops all robots"""
        resp = httpx.post(
            f"{API_URL}/api/robots/stop-all", 
            headers=auth_headers(super_admin_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        
        # Verify robots stopped
        status_resp = httpx.get(
            f"{API_URL}/api/robots/status", 
            headers=auth_headers(super_admin_token)
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["is_running"] is False
    
    def test_start_all_robots(self, super_admin_token):
        """POST /api/robots/start-all - starts all robots"""
        resp = httpx.post(
            f"{API_URL}/api/robots/start-all", 
            headers=auth_headers(super_admin_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data


# ============ TENANT OPERATIONS TEST ============
class TestTenantOperations:
    """Verify tenant operations still work correctly"""
    
    def test_get_products_with_tenant_token(self, tenant_token):
        """GET /api/products works with tenant token"""
        resp = httpx.get(
            f"{API_URL}/api/products", 
            headers=auth_headers(tenant_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
