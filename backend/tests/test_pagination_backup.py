"""
Test suite for Pagination APIs and Auto-Backup Settings
Tests: Products pagination, Customers pagination, Sales pagination, Backup auto-settings
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuthentication:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "password"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        print(f"LOGIN SUCCESS: Token received, user: {data['user']['email']}")
        return data["access_token"]


class TestProductsPagination:
    """Tests for Products pagination API"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "password"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_products_paginated_basic(self, auth_token):
        """Test paginated products endpoint returns correct structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products/paginated?page=1&page_size=10", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        assert "page" in data, "Missing 'page' in response"
        assert "page_size" in data, "Missing 'page_size' in response"
        assert "total_pages" in data, "Missing 'total_pages' in response"
        
        assert data["page"] == 1, f"Expected page 1, got {data['page']}"
        assert data["page_size"] == 10, f"Expected page_size 10, got {data['page_size']}"
        assert len(data["items"]) <= 10, f"Returned more items than page_size"
        
        print(f"PRODUCTS PAGINATED: total={data['total']}, page={data['page']}, total_pages={data['total_pages']}, items_returned={len(data['items'])}")
    
    def test_products_paginated_page_2(self, auth_token):
        """Test page 2 of products"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products/paginated?page=2&page_size=5", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["page"] == 2, f"Expected page 2, got {data['page']}"
        print(f"PRODUCTS PAGE 2: items_returned={len(data['items'])}")
    
    def test_products_paginated_custom_page_size(self, auth_token):
        """Test custom page_size"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products/paginated?page=1&page_size=20", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["page_size"] == 20, f"Expected page_size 20, got {data['page_size']}"
        assert len(data["items"]) <= 20, f"Returned more items than page_size"
        print(f"PRODUCTS CUSTOM PAGE SIZE: page_size={data['page_size']}, items={len(data['items'])}")
    
    def test_products_paginated_with_search(self, auth_token):
        """Test paginated products with search filter"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products/paginated?page=1&page_size=10&search=iPhone", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "items" in data
        print(f"PRODUCTS SEARCH 'iPhone': total={data['total']}, items={len(data['items'])}")


class TestCustomersPagination:
    """Tests for Customers pagination API"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "password"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_customers_paginated_basic(self, auth_token):
        """Test paginated customers endpoint returns correct structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/customers/paginated?page=1&page_size=10", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        assert "page" in data, "Missing 'page' in response"
        assert "page_size" in data, "Missing 'page_size' in response"
        assert "total_pages" in data, "Missing 'total_pages' in response"
        
        print(f"CUSTOMERS PAGINATED: total={data['total']}, page={data['page']}, total_pages={data['total_pages']}, items_returned={len(data['items'])}")
    
    def test_customers_paginated_page_2(self, auth_token):
        """Test page 2 of customers"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/customers/paginated?page=2&page_size=5", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["page"] == 2, f"Expected page 2, got {data['page']}"
        print(f"CUSTOMERS PAGE 2: items_returned={len(data['items'])}")


class TestSalesPagination:
    """Tests for Sales pagination API"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "password"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_sales_paginated_basic(self, auth_token):
        """Test paginated sales endpoint returns correct structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/sales/paginated?page=1&page_size=10", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        
        print(f"SALES PAGINATED: total={data['total']}, items_returned={len(data['items'])}")


class TestAutoBackupSettings:
    """Tests for Auto-Backup Settings API"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "password"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_auto_backup_settings(self, auth_token):
        """Test GET /api/backup/auto-settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/backup/auto-settings", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Should have default settings structure
        assert "enabled" in data, "Missing 'enabled' field"
        assert "frequency" in data, "Missing 'frequency' field"
        assert "time" in data, "Missing 'time' field"
        assert "keep_count" in data, "Missing 'keep_count' field"
        
        print(f"AUTO-BACKUP SETTINGS: enabled={data['enabled']}, frequency={data['frequency']}, time={data['time']}, keep_count={data['keep_count']}")
    
    def test_post_auto_backup_settings(self, auth_token):
        """Test POST /api/backup/auto-settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        settings = {
            "enabled": True,
            "frequency": "daily",
            "time": "04:00",
            "keep_count": 15
        }
        response = requests.post(f"{BASE_URL}/api/backup/auto-settings", json=settings, headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, f"Expected success=True, got {data}"
        
        print(f"AUTO-BACKUP SETTINGS SAVED: {data}")
        
        # Verify settings were saved by GET
        get_response = requests.get(f"{BASE_URL}/api/backup/auto-settings", headers=headers)
        assert get_response.status_code == 200
        saved_settings = get_response.json()
        assert saved_settings.get("enabled") == True, f"Settings not saved correctly"
        assert saved_settings.get("frequency") == "daily", f"Frequency not saved"
        print(f"AUTO-BACKUP SETTINGS VERIFIED: {saved_settings}")
    
    def test_run_auto_backup(self, auth_token):
        """Test POST /api/backup/run-auto"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/backup/run-auto", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "backup_id" in data or "success" in data, f"Unexpected response: {data}"
        print(f"AUTO-BACKUP RUN: {data}")


class TestSmartNotifications:
    """Tests for Smart Notifications"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "password"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_notifications_generate(self, auth_token):
        """Test POST /api/notifications/generate to create smart notifications"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/notifications/generate", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        print(f"NOTIFICATIONS GENERATE: {data}")
    
    def test_get_notifications(self, auth_token):
        """Test GET /api/notifications"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"NOTIFICATIONS: count={len(data)}")
        if data:
            print(f"Sample notification: {data[0]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
