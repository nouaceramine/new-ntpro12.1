"""
Tests for Iteration 53 Features:
1. POS Session Management - open/close session from POS
2. Dashboard Total Cash calculation
3. Backup System APIs for tenants
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test credentials - Tenant uses unified-login to get proper tenant context
TENANT_EMAIL = "ncr@ntcommerce.com"
TENANT_PASSWORD = "Test@123"
SUPER_ADMIN_EMAIL = "admin@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "Admin@2024"


class TestAuthentication:
    """Authentication tests"""
    
    def test_tenant_login(self):
        """Test tenant login using unified-login endpoint"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        assert response.status_code == 200, f"Tenant login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user_type") == "tenant", f"Expected tenant user type, got {data.get('user_type')}"
        print(f"Tenant login successful, user_type: {data.get('user_type')}")
    
    def test_super_admin_login(self):
        """Test super admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print(f"Super admin login successful")


class TestDashboardStats:
    """Test dashboard stats including total cash"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tenant using unified-login"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_stats_endpoint(self, auth_token):
        """Test /api/stats endpoint returns total_cash"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/stats", headers=headers)
        assert response.status_code == 200, f"Stats failed: {response.text}"
        data = response.json()
        
        # Check total_cash is present
        assert "total_cash" in data, "total_cash missing from stats"
        print(f"Total cash from stats: {data.get('total_cash')}")
        
        # Check cash_boxes array is present
        assert "cash_boxes" in data, "cash_boxes missing from stats"
        print(f"Cash boxes: {data.get('cash_boxes')}")
        
        # Verify total_cash is sum of cash box balances
        cash_boxes = data.get('cash_boxes', [])
        calculated_total = sum(b.get('balance', 0) for b in cash_boxes)
        assert data['total_cash'] == calculated_total, f"Total cash mismatch: {data['total_cash']} != {calculated_total}"
        print(f"PASS: Total cash calculation verified: {data['total_cash']} = sum of {len(cash_boxes)} cash boxes")
    
    def test_cash_boxes_endpoint(self, auth_token):
        """Test cash boxes API"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/cash-boxes", headers=headers)
        assert response.status_code == 200, f"Cash boxes failed: {response.text}"
        data = response.json()
        print(f"Cash boxes: {data}")


class TestPOSSessions:
    """Test POS session management"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_current_session(self, auth_token):
        """Test GET current session"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/daily-sessions/current", headers=headers)
        # Should return 200 even if no session (returns null) or with session
        assert response.status_code in [200, 404], f"Current session failed: {response.text}"
        print(f"Current session response: {response.status_code} - {response.text[:200]}")
    
    def test_generate_session_code(self, auth_token):
        """Test session code generation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/daily-sessions/generate-code", headers=headers)
        assert response.status_code == 200, f"Generate code failed: {response.text}"
        data = response.json()
        assert "code" in data, "No code in response"
        print(f"Generated session code: {data['code']}")
    
    def test_list_daily_sessions(self, auth_token):
        """Test list daily sessions"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/daily-sessions", headers=headers)
        assert response.status_code == 200, f"List sessions failed: {response.text}"
        print(f"Daily sessions count: {len(response.json()) if isinstance(response.json(), list) else 'N/A'}")


class TestBackupSystem:
    """Test backup system APIs for tenants"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_auto_backup_settings(self, auth_token):
        """Test GET auto-backup settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/backup/auto-settings", headers=headers)
        # Could be 200 or 404 if not configured
        assert response.status_code in [200, 404], f"Auto-backup settings failed: {response.text}"
        print(f"Auto-backup settings: {response.status_code} - {response.text[:200] if response.text else 'empty'}")
    
    def test_save_auto_backup_settings(self, auth_token):
        """Test POST auto-backup settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        settings = {
            "enabled": True,
            "frequency": "daily",
            "time": "02:00",
            "keep_count": 10
        }
        response = requests.post(f"{BASE_URL}/api/backup/auto-settings", headers=headers, json=settings)
        # Should return 200 or 201 on success
        assert response.status_code in [200, 201], f"Save auto-backup settings failed: {response.text}"
        print(f"Save auto-backup settings: {response.status_code}")
    
    def test_run_auto_backup(self, auth_token):
        """Test POST run-auto backup"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/backup/run-auto", headers=headers, json={})
        # Should return 200 on success
        assert response.status_code in [200, 201], f"Run auto backup failed: {response.text}"
        print(f"Run auto backup: {response.status_code}")


class TestProductsAPI:
    """Test products API for French language support"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_products_list(self, auth_token):
        """Test products list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200, f"Products list failed: {response.text}"
        data = response.json()
        print(f"Products count: {len(data) if isinstance(data, list) else 'N/A'}")
    
    def test_product_families(self, auth_token):
        """Test product families"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/product-families", headers=headers)
        assert response.status_code == 200, f"Product families failed: {response.text}"
        print(f"Product families: {response.json()}")
    
    def test_generate_article_code(self, auth_token):
        """Test article code generation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products/generate-article-code", headers=headers)
        assert response.status_code == 200, f"Generate article code failed: {response.text}"
        data = response.json()
        assert "article_code" in data, "No article_code in response"
        print(f"Generated article code: {data['article_code']}")
    
    def test_generate_barcode(self, auth_token):
        """Test barcode generation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products/generate-barcode", headers=headers)
        assert response.status_code == 200, f"Generate barcode failed: {response.text}"
        data = response.json()
        assert "barcode" in data, "No barcode in response"
        print(f"Generated barcode: {data['barcode']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
