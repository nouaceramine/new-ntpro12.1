"""
Test suite for iteration 32 - New features testing
Features to test:
1. Edit Product page matches Add Product page (image upload)
2. Unified sidebar for all users
3. Normal numbers format (not Arabic)
4. Quick Excel export button on products page
5. Monthly profit section on dashboard (/api/dashboard/profit-stats)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestProfitStatsAPI:
    """Test /api/dashboard/profit-stats endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_profit_stats_endpoint_exists(self):
        """Test that profit-stats endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/dashboard/profit-stats", headers=self.headers)
        assert response.status_code == 200, f"profit-stats returned {response.status_code}: {response.text}"
        print("✓ /api/dashboard/profit-stats endpoint exists and returns 200")
    
    def test_profit_stats_response_structure(self):
        """Test profit-stats response has correct fields"""
        response = requests.get(f"{BASE_URL}/api/dashboard/profit-stats", headers=self.headers)
        data = response.json()
        
        # Check all required fields exist
        assert "monthly_revenue" in data, "missing monthly_revenue field"
        assert "monthly_purchase_cost" in data, "missing monthly_purchase_cost field"
        assert "monthly_expenses" in data, "missing monthly_expenses field"
        assert "monthly_profit" in data, "missing monthly_profit field"
        
        print(f"✓ profit-stats response structure correct: {data}")
    
    def test_profit_stats_values_are_numbers(self):
        """Test profit-stats values are numeric"""
        response = requests.get(f"{BASE_URL}/api/dashboard/profit-stats", headers=self.headers)
        data = response.json()
        
        assert isinstance(data["monthly_revenue"], (int, float)), "monthly_revenue should be numeric"
        assert isinstance(data["monthly_purchase_cost"], (int, float)), "monthly_purchase_cost should be numeric"
        assert isinstance(data["monthly_expenses"], (int, float)), "monthly_expenses should be numeric"
        assert isinstance(data["monthly_profit"], (int, float)), "monthly_profit should be numeric"
        
        print("✓ All profit-stats values are numeric")
    
    def test_profit_calculation_formula(self):
        """Test that monthly_profit = monthly_revenue - monthly_purchase_cost - monthly_expenses"""
        response = requests.get(f"{BASE_URL}/api/dashboard/profit-stats", headers=self.headers)
        data = response.json()
        
        expected_profit = data["monthly_revenue"] - data["monthly_purchase_cost"] - data["monthly_expenses"]
        assert abs(data["monthly_profit"] - expected_profit) < 0.01, \
            f"Profit calculation incorrect: expected {expected_profit}, got {data['monthly_profit']}"
        
        print(f"✓ Profit calculation verified: {data['monthly_revenue']} - {data['monthly_purchase_cost']} - {data['monthly_expenses']} = {data['monthly_profit']}")


class TestSalesStatsAPI:
    """Test /api/dashboard/sales-stats endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_sales_stats_endpoint(self):
        """Test sales-stats endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/dashboard/sales-stats", headers=self.headers)
        assert response.status_code == 200, f"sales-stats returned {response.status_code}"
        print("✓ /api/dashboard/sales-stats endpoint works")


class TestProductsAPI:
    """Test products-related endpoints for edit product page features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_products(self):
        """Test getting products list"""
        response = requests.get(f"{BASE_URL}/api/products", headers=self.headers)
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)
        print(f"✓ Products list retrieved: {len(products)} products")
    
    def test_product_has_image_url_field(self):
        """Test that products have image_url field (for edit page)"""
        response = requests.get(f"{BASE_URL}/api/products", headers=self.headers)
        products = response.json()
        
        if products:
            product = products[0]
            assert "image_url" in product, "Product should have image_url field"
            print(f"✓ Product has image_url field: {product.get('image_url', '')[:50]}...")
        else:
            print("! No products to test image_url field")
    
    def test_product_has_family_id_field(self):
        """Test that products have family_id field"""
        response = requests.get(f"{BASE_URL}/api/products", headers=self.headers)
        products = response.json()
        
        if products:
            product = products[0]
            assert "family_id" in product, "Product should have family_id field"
            assert "family_name" in product, "Product should have family_name field"
            print(f"✓ Product has family fields: family_id={product.get('family_id')}, family_name={product.get('family_name')}")
        else:
            print("! No products to test family fields")
    
    def test_update_product_with_image(self):
        """Test updating product image_url"""
        # First get a product
        response = requests.get(f"{BASE_URL}/api/products", headers=self.headers)
        products = response.json()
        
        if not products:
            pytest.skip("No products to test update")
        
        product_id = products[0]["id"]
        
        # Update the product
        update_data = {
            "image_url": "https://example.com/test-image.jpg"
        }
        update_response = requests.put(
            f"{BASE_URL}/api/products/{product_id}", 
            json=update_data,
            headers=self.headers
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated_product = update_response.json()
        assert updated_product["image_url"] == "https://example.com/test-image.jpg"
        print(f"✓ Product image_url updated successfully")
    
    def test_generate_article_code(self):
        """Test article code generation endpoint"""
        response = requests.get(f"{BASE_URL}/api/products/generate-article-code", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "article_code" in data
        assert data["article_code"].startswith("AR")
        print(f"✓ Article code generated: {data['article_code']}")
    
    def test_generate_barcode(self):
        """Test barcode generation endpoint"""
        response = requests.get(f"{BASE_URL}/api/products/generate-barcode", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "barcode" in data
        assert len(data["barcode"]) == 13  # EAN-13 format
        print(f"✓ Barcode generated: {data['barcode']}")


class TestProductFamiliesAPI:
    """Test product families for edit product page"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_product_families(self):
        """Test getting product families list"""
        response = requests.get(f"{BASE_URL}/api/product-families", headers=self.headers)
        assert response.status_code == 200
        families = response.json()
        assert isinstance(families, list)
        print(f"✓ Product families retrieved: {len(families)} families")


class TestStatsAPI:
    """Test dashboard stats endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_stats_endpoint(self):
        """Test /api/stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check expected fields
        expected_fields = ["total_products", "total_customers", "total_suppliers", "low_stock_count"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Stats endpoint works: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
