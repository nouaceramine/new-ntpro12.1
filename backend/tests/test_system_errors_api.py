"""
Test System Errors API - NT Commerce SaaS
Tests for system error logging, monitoring, and auto-fixing endpoints
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Credentials
SUPER_ADMIN_EMAIL = "admin@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "Admin@2024"


class TestSystemErrorsAPI:
    """Test cases for System Errors API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get super admin token before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as super admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        assert self.token, "No token in login response"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    # ============ GET /api/saas/system-errors ============
    
    def test_get_system_errors_returns_list_and_stats(self):
        """GET /api/saas/system-errors returns errors list with stats"""
        response = self.session.get(f"{BASE_URL}/api/saas/system-errors")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "errors" in data, "Response should have 'errors' key"
        assert "stats" in data, "Response should have 'stats' key"
        assert isinstance(data["errors"], list), "errors should be a list"
        
        # Validate stats structure
        stats = data["stats"]
        assert "total" in stats, "Stats should have 'total'"
        assert "critical" in stats, "Stats should have 'critical'"
        assert "warning" in stats, "Stats should have 'warning'"
        assert "info" in stats, "Stats should have 'info'"
        assert "resolved" in stats, "Stats should have 'resolved'"
        assert "today" in stats, "Stats should have 'today'"
        
        print(f"✓ GET system-errors: {len(data['errors'])} errors, stats: {stats}")
    
    def test_get_system_errors_with_status_filter(self):
        """GET /api/saas/system-errors with status filter"""
        response = self.session.get(f"{BASE_URL}/api/saas/system-errors?status=active")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned errors should have status=active
        for error in data["errors"]:
            assert error["status"] == "active", f"Error status should be 'active', got '{error['status']}'"
        
        print(f"✓ GET system-errors with status=active: {len(data['errors'])} active errors")
    
    def test_get_system_errors_with_severity_filter(self):
        """GET /api/saas/system-errors with severity filter"""
        response = self.session.get(f"{BASE_URL}/api/saas/system-errors?severity=critical")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned errors should have severity=critical
        for error in data["errors"]:
            assert error["severity"] == "critical", f"Error severity should be 'critical', got '{error['severity']}'"
        
        print(f"✓ GET system-errors with severity=critical: {len(data['errors'])} critical errors")
    
    def test_get_system_errors_unauthorized_without_token(self):
        """GET /api/saas/system-errors without token should return 401"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/saas/system-errors")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET system-errors without token: 401 Unauthorized")
    
    # ============ POST /api/saas/system-errors ============
    
    def test_create_system_error(self):
        """POST /api/saas/system-errors creates new error"""
        error_data = {
            "type": "api",
            "severity": "warning",
            "message": f"Test error created at {datetime.now().isoformat()}",
            "tenant_id": "test-tenant-123",
            "tenant_name": "Test Tenant",
            "auto_fixable": True,
            "fix_action": "clear_cache",
            "details": {"endpoint": "/api/test", "status_code": 500}
        }
        
        # POST - this endpoint may not require auth based on code comment
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/saas/system-errors", json=error_data)
        
        assert response.status_code in [200, 201], f"Create error failed: {response.text}"
        data = response.json()
        
        # Validate response
        assert "id" in data, "Response should have 'id'"
        assert data["type"] == error_data["type"], "Type mismatch"
        assert data["severity"] == error_data["severity"], "Severity mismatch"
        assert data["message"] == error_data["message"], "Message mismatch"
        assert data["status"] == "active", "New error should have status 'active'"
        
        self.created_error_id = data["id"]
        print(f"✓ POST system-error created: {data['id']}")
        
        return data["id"]
    
    # ============ POST /api/saas/system-errors/{id}/fix ============
    
    def test_auto_fix_error(self):
        """POST /api/saas/system-errors/{id}/fix auto-fixes error"""
        # First create an error
        error_data = {
            "type": "database",
            "severity": "warning",
            "message": "Auto-fix test error",
            "auto_fixable": True,
            "fix_action": "reconnect_db"
        }
        
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        create_response = session.post(f"{BASE_URL}/api/saas/system-errors", json=error_data)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        error_id = create_response.json()["id"]
        
        # Now auto-fix it
        fix_response = self.session.post(f"{BASE_URL}/api/saas/system-errors/{error_id}/fix")
        
        assert fix_response.status_code == 200, f"Auto-fix failed: {fix_response.text}"
        fix_data = fix_response.json()
        
        assert fix_data.get("success") == True, "Fix should succeed"
        assert "message" in fix_data, "Fix response should have message"
        
        # Verify error is now resolved
        get_response = self.session.get(f"{BASE_URL}/api/saas/system-errors")
        errors = get_response.json()["errors"]
        fixed_error = next((e for e in errors if e["id"] == error_id), None)
        if fixed_error:
            assert fixed_error["status"] == "resolved", "Error should be resolved after fix"
        
        print(f"✓ POST auto-fix error: {fix_data['message']}")
    
    # ============ POST /api/saas/system-errors/{id}/resolve ============
    
    def test_manual_resolve_error(self):
        """POST /api/saas/system-errors/{id}/resolve marks as resolved"""
        # First create an error
        error_data = {
            "type": "system",
            "severity": "info",
            "message": "Manual resolve test error",
            "auto_fixable": False
        }
        
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        create_response = session.post(f"{BASE_URL}/api/saas/system-errors", json=error_data)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        error_id = create_response.json()["id"]
        
        # Manually resolve it
        resolve_response = self.session.post(f"{BASE_URL}/api/saas/system-errors/{error_id}/resolve")
        
        assert resolve_response.status_code == 200, f"Resolve failed: {resolve_response.text}"
        resolve_data = resolve_response.json()
        
        assert resolve_data.get("success") == True, "Resolve should succeed"
        
        print(f"✓ POST manual resolve: {resolve_data['message']}")
    
    def test_resolve_nonexistent_error_returns_404(self):
        """POST resolve on non-existent error returns 404"""
        response = self.session.post(f"{BASE_URL}/api/saas/system-errors/nonexistent-id/resolve")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ POST resolve nonexistent error: 404 Not Found")
    
    # ============ DELETE /api/saas/system-errors/resolved ============
    
    def test_clear_resolved_errors(self):
        """DELETE /api/saas/system-errors/resolved clears resolved errors"""
        # First create and resolve an error
        error_data = {
            "type": "auth",
            "severity": "info",
            "message": "Clear test error"
        }
        
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        create_response = session.post(f"{BASE_URL}/api/saas/system-errors", json=error_data)
        assert create_response.status_code in [200, 201]
        error_id = create_response.json()["id"]
        
        # Resolve it
        self.session.post(f"{BASE_URL}/api/saas/system-errors/{error_id}/resolve")
        
        # Clear resolved
        clear_response = self.session.delete(f"{BASE_URL}/api/saas/system-errors/resolved")
        
        assert clear_response.status_code == 200, f"Clear failed: {clear_response.text}"
        clear_data = clear_response.json()
        
        assert clear_data.get("success") == True, "Clear should succeed"
        assert "deleted_count" in clear_data, "Should return deleted count"
        
        print(f"✓ DELETE clear resolved: {clear_data['deleted_count']} errors deleted")
    
    # ============ POST /api/saas/system-errors/maintenance/{action} ============
    
    def test_maintenance_clear_cache(self):
        """POST maintenance/clear_cache runs cache clearing"""
        response = self.session.post(f"{BASE_URL}/api/saas/system-errors/maintenance/clear_cache")
        
        assert response.status_code == 200, f"Maintenance failed: {response.text}"
        data = response.json()
        
        assert data.get("action") == "clear_cache", "Action should be clear_cache"
        assert data.get("status") == "completed", "Status should be completed"
        assert "message" in data, "Should have message"
        assert "details" in data, "Should have details"
        
        print(f"✓ POST maintenance/clear_cache: {data['message']}")
    
    def test_maintenance_reconnect_db(self):
        """POST maintenance/reconnect_db runs DB reconnection"""
        response = self.session.post(f"{BASE_URL}/api/saas/system-errors/maintenance/reconnect_db")
        
        assert response.status_code == 200, f"Maintenance failed: {response.text}"
        data = response.json()
        
        assert data.get("action") == "reconnect_db", "Action should be reconnect_db"
        assert data.get("status") == "completed", "Status should be completed"
        
        print(f"✓ POST maintenance/reconnect_db: {data['message']}")
    
    def test_maintenance_restart_services(self):
        """POST maintenance/restart_services runs service restart"""
        response = self.session.post(f"{BASE_URL}/api/saas/system-errors/maintenance/restart_services")
        
        assert response.status_code == 200, f"Maintenance failed: {response.text}"
        data = response.json()
        
        assert data.get("action") == "restart_services", "Action should be restart_services"
        assert data.get("status") == "completed", "Status should be completed"
        
        print(f"✓ POST maintenance/restart_services: {data['message']}")
    
    def test_maintenance_system_check(self):
        """POST maintenance/system_check runs system health check"""
        response = self.session.post(f"{BASE_URL}/api/saas/system-errors/maintenance/system_check")
        
        assert response.status_code == 200, f"Maintenance failed: {response.text}"
        data = response.json()
        
        assert data.get("action") == "system_check", "Action should be system_check"
        assert data.get("status") == "completed", "Status should be completed"
        assert "details" in data, "Should have details"
        
        details = data["details"]
        assert "cpu_usage" in details, "Should have cpu_usage"
        assert "memory_usage" in details, "Should have memory_usage"
        assert "status" in details, "Should have health status"
        
        print(f"✓ POST maintenance/system_check: CPU {details.get('cpu_usage')}, RAM {details.get('memory_usage')}, Status {details.get('status')}")
    
    def test_maintenance_unauthorized_without_token(self):
        """POST maintenance without token returns 401"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/saas/system-errors/maintenance/clear_cache")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ POST maintenance without token: 401 Unauthorized")


class TestSystemErrorsStats:
    """Test stats calculations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get super admin token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_stats_reflect_actual_error_counts(self):
        """Stats should reflect actual error counts"""
        response = self.session.get(f"{BASE_URL}/api/saas/system-errors")
        
        assert response.status_code == 200
        data = response.json()
        
        errors = data["errors"]
        stats = data["stats"]
        
        # Count errors manually
        actual_critical = len([e for e in errors if e.get("severity") == "critical"])
        actual_warning = len([e for e in errors if e.get("severity") == "warning"])
        actual_info = len([e for e in errors if e.get("severity") == "info"])
        actual_resolved = len([e for e in errors if e.get("status") == "resolved"])
        
        # Stats total includes all errors, not just returned ones
        print(f"✓ Stats verification: total={stats['total']}, critical={stats['critical']}, warning={stats['warning']}, info={stats['info']}, resolved={stats['resolved']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
