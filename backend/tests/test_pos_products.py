"""
NT Commerce Backend Tests - POS and Products
Tests for products CRUD, search, and POS-related functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://legendary-build-1.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "demo@demo.com"
TEST_PASSWORD = "demo123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tenant user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/unified-login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data["access_token"]


@pytest.fixture
def authenticated_client(auth_token):
    """Returns a session with auth headers"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_unified_login_success(self):
        """Test unified login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/unified-login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "user_type" in data
        assert data["user_type"] == "tenant"
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        
    def test_unified_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/unified-login",
            json={"email": "invalid@test.com", "password": "wrongpass"}
        )
        assert response.status_code == 401


class TestProducts:
    """Product CRUD tests"""
    
    def test_get_products(self, authenticated_client):
        """Test fetching all products"""
        response = authenticated_client.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Check product structure if products exist
        if len(data) > 0:
            product = data[0]
            assert "id" in product
            assert "name_ar" in product or "name_en" in product
            assert "retail_price" in product
            assert "quantity" in product
            
    def test_create_product(self, authenticated_client):
        """Test creating a new product"""
        product_data = {
            "name_ar": "منتج اختبار API",
            "name_en": "API Test Product",
            "retail_price": 250,
            "wholesale_price": 200,
            "purchase_price": 150,
            "quantity": 30,
            "barcode": "TEST_API_123"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/products",
            json=product_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name_ar"] == product_data["name_ar"]
        assert data["retail_price"] == product_data["retail_price"]
        assert data["quantity"] == product_data["quantity"]
        assert "id" in data
        
        # Cleanup - delete the test product
        product_id = data["id"]
        authenticated_client.delete(f"{BASE_URL}/api/products/{product_id}")
        
    def test_search_products_by_name(self, authenticated_client):
        """Test searching products by name"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/products",
            params={"search": "سامسونج"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # If products match, they should contain the search term
        
    def test_search_products_by_barcode(self, authenticated_client):
        """Test searching products by barcode"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/products",
            params={"search": "123456789"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
    def test_quick_search_products(self, authenticated_client):
        """Test quick search endpoint"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/products/quick-search",
            params={"q": "سامسونج", "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "total" in data
        
    def test_generate_article_code(self, authenticated_client):
        """Test article code generation"""
        response = authenticated_client.get(f"{BASE_URL}/api/products/generate-article-code")
        assert response.status_code == 200
        
        data = response.json()
        assert "article_code" in data
        assert data["article_code"].startswith("AR")
        
    def test_generate_barcode(self, authenticated_client):
        """Test barcode generation"""
        response = authenticated_client.get(f"{BASE_URL}/api/products/generate-barcode")
        assert response.status_code == 200
        
        data = response.json()
        assert "barcode" in data
        # EAN-13 barcode should be 13 digits
        assert len(data["barcode"]) == 13


class TestCustomers:
    """Customer CRUD tests"""
    
    def test_get_customers(self, authenticated_client):
        """Test fetching all customers"""
        response = authenticated_client.get(f"{BASE_URL}/api/customers")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
    def test_generate_customer_code(self, authenticated_client):
        """Test customer code generation"""
        response = authenticated_client.get(f"{BASE_URL}/api/customers/generate-code")
        assert response.status_code == 200
        
        data = response.json()
        assert "code" in data
        assert data["code"].startswith("CL")


class TestSales:
    """Sales code generation tests"""
    
    def test_generate_sale_code(self, authenticated_client):
        """Test sale code generation"""
        response = authenticated_client.get(f"{BASE_URL}/api/sales/generate-code")
        assert response.status_code == 200
        
        data = response.json()
        assert "code" in data
        assert data["code"].startswith("BV")


class TestProductFamilies:
    """Product families tests"""
    
    def test_get_product_families(self, authenticated_client):
        """Test fetching product families"""
        response = authenticated_client.get(f"{BASE_URL}/api/product-families")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestWarehouses:
    """Warehouse tests"""
    
    def test_get_warehouses(self, authenticated_client):
        """Test fetching warehouses"""
        response = authenticated_client.get(f"{BASE_URL}/api/warehouses")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestDailySessions:
    """Daily session tests"""
    
    def test_check_current_session(self, authenticated_client):
        """Test checking current daily session"""
        response = authenticated_client.get(f"{BASE_URL}/api/daily-sessions/current")
        # May return 200 with session data or 404 if no session
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
