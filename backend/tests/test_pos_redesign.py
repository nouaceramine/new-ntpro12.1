"""
POS Page Redesign Tests
Tests for the redesigned Point of Sale functionality
Using synchronous requests for simplicity
"""
import requests
import pytest
from datetime import datetime

# Test configuration
BASE_URL = "https://checkout-flow-76.preview.emergentagent.com/api"
TEST_USER = {"email": "test@test.com", "password": "test123"}


class TestPOSBasicAPIs:
    """Test basic POS-related API endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for API calls"""
        response = requests.post(
            f"{BASE_URL}/auth/unified-login",
            json=TEST_USER
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        return None
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        if auth_token:
            return {"Authorization": f"Bearer {auth_token}"}
        return {}
    
    def test_login(self):
        """Test user login"""
        response = requests.post(
            f"{BASE_URL}/auth/unified-login",
            json=TEST_USER
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data.get("user_type") in ["admin", "user", "tenant"]
    
    def test_get_products(self, auth_headers):
        """Test fetching products list"""
        response = requests.get(
            f"{BASE_URL}/products",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_customers(self, auth_headers):
        """Test fetching customers list"""
        response = requests.get(
            f"{BASE_URL}/customers",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_warehouses(self, auth_headers):
        """Test fetching warehouses list"""
        response = requests.get(
            f"{BASE_URL}/warehouses",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_product_families(self, auth_headers):
        """Test fetching product families"""
        response = requests.get(
            f"{BASE_URL}/product-families",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestPOSSalesAPIs:
    """Test POS sales-related API endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for API calls"""
        response = requests.post(
            f"{BASE_URL}/auth/unified-login",
            json=TEST_USER
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        return None
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        if auth_token:
            return {"Authorization": f"Bearer {auth_token}"}
        return {}
    
    def test_generate_sale_code(self, auth_headers):
        """Test generating sale code"""
        response = requests.get(
            f"{BASE_URL}/sales/generate-code",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert data["code"].startswith("BV")
    
    def test_get_current_session(self, auth_headers):
        """Test checking current daily session"""
        response = requests.get(
            f"{BASE_URL}/daily-sessions/current",
            headers=auth_headers
        )
        # Either 200 with session data or 404 if no session
        assert response.status_code in [200, 404]
    
    def test_get_wilayas(self, auth_headers):
        """Test fetching delivery wilayas"""
        response = requests.get(
            f"{BASE_URL}/delivery/wilayas",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestPOSCustomerAPIs:
    """Test customer-related API endpoints for POS"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for API calls"""
        response = requests.post(
            f"{BASE_URL}/auth/unified-login",
            json=TEST_USER
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        return None
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        if auth_token:
            return {"Authorization": f"Bearer {auth_token}"}
        return {}
    
    def test_get_customer_families(self, auth_headers):
        """Test fetching customer families"""
        response = requests.get(
            f"{BASE_URL}/customer-families",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_customer(self, auth_headers):
        """Test creating a new customer from POS"""
        timestamp = datetime.now().strftime("%H%M%S")
        customer_data = {
            "name": f"Test Customer {timestamp}",
            "phone": f"05{timestamp}",
            "email": f"test{timestamp}@example.com"
        }
        response = requests.post(
            f"{BASE_URL}/customers",
            json=customer_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data


class TestPOSSettingsAPIs:
    """Test settings-related API endpoints for POS"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for API calls"""
        response = requests.post(
            f"{BASE_URL}/auth/unified-login",
            json=TEST_USER
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        return None
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        if auth_token:
            return {"Authorization": f"Bearer {auth_token}"}
        return {}
    
    def test_get_receipt_settings(self, auth_headers):
        """Test fetching receipt settings"""
        response = requests.get(
            f"{BASE_URL}/settings/receipt",
            headers=auth_headers
        )
        # Settings might not exist yet
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
