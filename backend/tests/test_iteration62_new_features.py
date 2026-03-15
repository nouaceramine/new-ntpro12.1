"""
Test Iteration 62: New Features
- 3 new robots (customer, pricing, maintenance) for 6 total
- Auto-Reports API endpoints
- Brute-force protection (5 failed attempts = 429 lockout)
"""
import pytest
import httpx
import time
import uuid

API_URL = "https://nt-commerce-refactor.preview.emergentagent.com"

# ============ CREDENTIALS ============
SUPER_ADMIN_EMAIL = "admin@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "Admin@2024"
TENANT_EMAIL = "ncr@ntcommerce.com"
TENANT_PASSWORD = "Test@123"

# Use unique email for brute force testing to avoid locking real accounts
BRUTE_FORCE_TEST_EMAIL = f"TEST_bruteforce_{uuid.uuid4().hex[:6]}@test.com"


# ============ FIXTURES ============
@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin token for testing"""
    resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
        "email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD
    })
    assert resp.status_code == 200, f"Super admin login failed: {resp.text}"
    data = resp.json()
    assert "access_token" in data
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


# ============ ROBOT STATUS - ALL 6 ROBOTS ============
class TestAllSixRobots:
    """Verify all 6 robots (inventory, debt, report, customer, pricing, maintenance) are present"""
    
    def test_get_status_returns_6_robots(self, super_admin_token):
        """GET /api/robots/status returns all 6 robots"""
        resp = httpx.get(f"{API_URL}/api/robots/status", headers=auth_headers(super_admin_token))
        assert resp.status_code == 200, f"Failed to get robot status: {resp.text}"
        data = resp.json()
        
        # Verify structure
        assert "is_running" in data
        assert "robots" in data
        
        # Verify all 6 robots are present
        robots = data["robots"]
        expected_robots = ["inventory", "debt", "report", "customer", "pricing", "maintenance"]
        for robot_name in expected_robots:
            assert robot_name in robots, f"Robot '{robot_name}' missing from status"
            robot = robots[robot_name]
            assert "name" in robot, f"{robot_name} missing 'name'"
            assert "is_running" in robot, f"{robot_name} missing 'is_running'"
            assert "stats" in robot, f"{robot_name} missing 'stats'"
        
        print(f"All 6 robots found: {list(robots.keys())}")
    
    def test_customer_robot_has_expected_stats(self, super_admin_token):
        """Customer robot should have expected stat fields"""
        resp = httpx.get(f"{API_URL}/api/robots/status", headers=auth_headers(super_admin_token))
        data = resp.json()
        customer = data["robots"].get("customer", {})
        stats = customer.get("stats", {})
        # Customer robot stats: checks, segments_updated, inactive_found, vip_found
        assert "checks" in stats, "Customer robot missing 'checks' stat"
        print(f"Customer robot stats: {stats}")
    
    def test_pricing_robot_has_expected_stats(self, super_admin_token):
        """Pricing robot should have expected stat fields"""
        resp = httpx.get(f"{API_URL}/api/robots/status", headers=auth_headers(super_admin_token))
        data = resp.json()
        pricing = data["robots"].get("pricing", {})
        stats = pricing.get("stats", {})
        # Pricing robot stats: checks, recommendations, slow_movers, margin_alerts
        assert "checks" in stats, "Pricing robot missing 'checks' stat"
        print(f"Pricing robot stats: {stats}")
    
    def test_maintenance_robot_has_expected_stats(self, super_admin_token):
        """Maintenance robot should have expected stat fields"""
        resp = httpx.get(f"{API_URL}/api/robots/status", headers=auth_headers(super_admin_token))
        data = resp.json()
        maintenance = data["robots"].get("maintenance", {})
        stats = maintenance.get("stats", {})
        # Maintenance robot stats: checks, records_cleaned, indexes_created, health_checks
        assert "checks" in stats, "Maintenance robot missing 'checks' stat"
        print(f"Maintenance robot stats: {stats}")


# ============ NEW ROBOT RUN ENDPOINTS ============
class TestNewRobotRunEndpoints:
    """Test run endpoints for new robots"""
    
    def test_run_customer_robot(self, super_admin_token):
        """POST /api/robots/run/customer triggers customer analysis"""
        resp = httpx.post(
            f"{API_URL}/api/robots/run/customer",
            headers=auth_headers(super_admin_token),
            timeout=30.0
        )
        assert resp.status_code == 200, f"Failed to run customer robot: {resp.text}"
        data = resp.json()
        assert "stats" in data
        print(f"Customer robot run result: {data}")
    
    def test_run_pricing_robot(self, super_admin_token):
        """POST /api/robots/run/pricing triggers pricing analysis"""
        resp = httpx.post(
            f"{API_URL}/api/robots/run/pricing",
            headers=auth_headers(super_admin_token),
            timeout=30.0
        )
        assert resp.status_code == 200, f"Failed to run pricing robot: {resp.text}"
        data = resp.json()
        assert "stats" in data
        print(f"Pricing robot run result: {data}")
    
    def test_run_maintenance_robot(self, super_admin_token):
        """POST /api/robots/run/maintenance triggers maintenance tasks"""
        resp = httpx.post(
            f"{API_URL}/api/robots/run/maintenance",
            headers=auth_headers(super_admin_token),
            timeout=30.0
        )
        assert resp.status_code == 200, f"Failed to run maintenance robot: {resp.text}"
        data = resp.json()
        assert "stats" in data
        print(f"Maintenance robot run result: {data}")
    
    def test_run_report_robot_generates_daily_report(self, super_admin_token):
        """POST /api/robots/run/report generates a daily report"""
        resp = httpx.post(
            f"{API_URL}/api/robots/run/report",
            headers=auth_headers(super_admin_token),
            timeout=30.0
        )
        assert resp.status_code == 200, f"Failed to run report robot: {resp.text}"
        data = resp.json()
        assert "stats" in data
        print(f"Report robot run result: {data}")


# ============ AUTO-REPORTS API ============
class TestAutoReportsAPI:
    """Test auto-reports endpoints"""
    
    def test_get_auto_reports_list(self, super_admin_token):
        """GET /api/auto-reports returns list of reports"""
        resp = httpx.get(
            f"{API_URL}/api/auto-reports",
            headers=auth_headers(super_admin_token)
        )
        assert resp.status_code == 200, f"Failed to get auto-reports: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "auto-reports should return a list"
        print(f"Auto-reports count: {len(data)}")
        if data:
            print(f"Sample report keys: {list(data[0].keys())}")
    
    def test_get_auto_reports_filter_by_daily(self, super_admin_token):
        """GET /api/auto-reports?report_type=daily filters by daily type"""
        resp = httpx.get(
            f"{API_URL}/api/auto-reports?report_type=daily",
            headers=auth_headers(super_admin_token)
        )
        assert resp.status_code == 200, f"Failed to filter auto-reports: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        for report in data:
            assert report.get("type") == "daily", f"Expected daily report, got {report.get('type')}"
        print(f"Daily reports count: {len(data)}")
    
    def test_get_auto_reports_filter_by_weekly(self, super_admin_token):
        """GET /api/auto-reports?report_type=weekly filters by weekly type"""
        resp = httpx.get(
            f"{API_URL}/api/auto-reports?report_type=weekly",
            headers=auth_headers(super_admin_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for report in data:
            assert report.get("type") == "weekly"
        print(f"Weekly reports count: {len(data)}")
    
    def test_get_auto_reports_filter_by_monthly(self, super_admin_token):
        """GET /api/auto-reports?report_type=monthly filters by monthly type"""
        resp = httpx.get(
            f"{API_URL}/api/auto-reports?report_type=monthly",
            headers=auth_headers(super_admin_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for report in data:
            assert report.get("type") == "monthly"
        print(f"Monthly reports count: {len(data)}")
    
    def test_auto_reports_require_super_admin(self, tenant_token):
        """GET /api/auto-reports with tenant token returns 403"""
        resp = httpx.get(
            f"{API_URL}/api/auto-reports",
            headers=auth_headers(tenant_token)
        )
        assert resp.status_code == 403, "Auto-reports should require super_admin"


# ============ COLLECTION REPORTS API ============
class TestCollectionReportsAPI:
    """Test collection reports endpoint"""
    
    def test_get_collection_reports(self, super_admin_token):
        """GET /api/collection-reports returns list"""
        resp = httpx.get(
            f"{API_URL}/api/collection-reports",
            headers=auth_headers(super_admin_token)
        )
        assert resp.status_code == 200, f"Failed to get collection-reports: {resp.text}"
        data = resp.json()
        assert isinstance(data, list)
        print(f"Collection reports count: {len(data)}")
    
    def test_collection_reports_require_super_admin(self, tenant_token):
        """GET /api/collection-reports with tenant token returns 403"""
        resp = httpx.get(
            f"{API_URL}/api/collection-reports",
            headers=auth_headers(tenant_token)
        )
        assert resp.status_code == 403


# ============ BRUTE FORCE PROTECTION ============
class TestBruteForceProtection:
    """Test brute force protection on unified-login endpoint"""
    
    def test_normal_admin_login_still_works(self):
        """Normal admin login should still work"""
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD
        })
        assert resp.status_code == 200, f"Admin login failed: {resp.text}"
        assert "access_token" in resp.json()
        print("Admin login successful after brute force tests")
    
    def test_normal_tenant_login_still_works(self):
        """Normal tenant login should still work"""
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL, "password": TENANT_PASSWORD
        })
        assert resp.status_code == 200, f"Tenant login failed: {resp.text}"
        assert "access_token" in resp.json()
        print("Tenant login successful after brute force tests")
    
    def test_brute_force_lockout_after_5_attempts(self):
        """After 5 failed attempts, 6th should return 429"""
        # Use unique email to avoid affecting real accounts
        test_email = BRUTE_FORCE_TEST_EMAIL
        
        # Make 5 failed login attempts
        for i in range(5):
            resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
                "email": test_email, "password": "wrongpassword"
            })
            # Should get 401/404 for invalid credentials
            assert resp.status_code in [401, 404], f"Attempt {i+1} got unexpected {resp.status_code}"
            print(f"Failed attempt {i+1}: status {resp.status_code}")
        
        # 6th attempt should be locked out (429)
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": test_email, "password": "wrongpassword"
        })
        assert resp.status_code == 429, f"Expected 429 lockout, got {resp.status_code}"
        print(f"Brute force protection triggered: {resp.json()}")
    
    def test_lockout_message_in_arabic(self):
        """Lockout message should be in Arabic"""
        # Use different unique email
        test_email = f"TEST_lockout_{uuid.uuid4().hex[:6]}@test.com"
        
        # Make 5 failed attempts
        for i in range(5):
            httpx.post(f"{API_URL}/api/auth/unified-login", json={
                "email": test_email, "password": "wrong"
            })
        
        # Check 6th attempt response
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": test_email, "password": "wrong"
        })
        assert resp.status_code == 429
        data = resp.json()
        detail = data.get("detail", "")
        # Should contain Arabic text about lockout
        assert "الحساب مقفل" in detail or "دقيقة" in detail, f"Expected Arabic lockout message, got: {detail}"
        print(f"Arabic lockout message: {detail}")


# ============ ROBOT RESTART ENDPOINTS FOR NEW ROBOTS ============
class TestNewRobotRestartEndpoints:
    """Test restart endpoints for new robots"""
    
    def test_restart_customer_robot(self, super_admin_token):
        """POST /api/robots/restart/customer works"""
        resp = httpx.post(
            f"{API_URL}/api/robots/restart/customer",
            headers=auth_headers(super_admin_token),
            timeout=10.0
        )
        assert resp.status_code == 200, f"Failed to restart customer robot: {resp.text}"
        assert "message" in resp.json()
    
    def test_restart_pricing_robot(self, super_admin_token):
        """POST /api/robots/restart/pricing works"""
        resp = httpx.post(
            f"{API_URL}/api/robots/restart/pricing",
            headers=auth_headers(super_admin_token),
            timeout=10.0
        )
        assert resp.status_code == 200, f"Failed to restart pricing robot: {resp.text}"
        assert "message" in resp.json()
    
    def test_restart_maintenance_robot(self, super_admin_token):
        """POST /api/robots/restart/maintenance works"""
        resp = httpx.post(
            f"{API_URL}/api/robots/restart/maintenance",
            headers=auth_headers(super_admin_token),
            timeout=10.0
        )
        assert resp.status_code == 200, f"Failed to restart maintenance robot: {resp.text}"
        assert "message" in resp.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
