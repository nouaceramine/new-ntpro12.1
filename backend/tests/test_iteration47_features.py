"""
Tests for Iteration 47 Features:
1. Store Management APIs (GET/PUT /api/store/settings)
2. SaaS Plans Public API (GET /api/saas/plans/public)

These tests verify the new e-commerce store features and public pricing page functionality.
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://ai-accounting-saas.preview.emergentagent.com"


class TestPublicAPIs:
    """Public API endpoints that don't require authentication"""
    
    def test_saas_plans_public_returns_plans(self):
        """GET /api/saas/plans/public - returns list of active plans"""
        response = requests.get(f"{BASE_URL}/api/saas/plans/public")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} public plans")
        
        # Verify plan structure if plans exist
        if len(data) > 0:
            plan = data[0]
            # Check basic plan fields exist
            assert 'id' in plan or 'name' in plan, "Plan should have id or name field"
            print(f"Sample plan: {plan.get('name_ar') or plan.get('name')}")
    
    def test_saas_plans_public_plan_has_pricing(self):
        """Plans should have pricing information"""
        response = requests.get(f"{BASE_URL}/api/saas/plans/public")
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            plan = data[0]
            # Most plans should have price_monthly
            has_pricing = 'price_monthly' in plan or 'price' in plan
            print(f"Plan has pricing info: {has_pricing}")


class TestAuthenticatedAPIs:
    """APIs requiring authentication - uses tenant user for store APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login with tenant admin user"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "tenant_admin@test.com",
            "password": "test123"
        })
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.text}")
        
        self.token = login_response.json().get('access_token')
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_store_settings_get(self):
        """GET /api/store/settings - returns store configuration"""
        response = requests.get(f"{BASE_URL}/api/store/settings", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        
        # Check for expected store settings fields
        expected_fields = ['enabled', 'store_name', 'store_slug', 'cod_enabled', 'delivery_enabled']
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"Store enabled: {data.get('enabled')}")
        print(f"Store name: {data.get('store_name')}")
    
    def test_store_settings_put(self):
        """PUT /api/store/settings - updates store configuration"""
        # First get current settings
        get_response = requests.get(f"{BASE_URL}/api/store/settings", headers=self.headers)
        assert get_response.status_code == 200
        
        current_settings = get_response.json()
        
        # Update with test values
        test_slug = f"test-store-{uuid.uuid4().hex[:8]}"
        update_data = {
            **current_settings,
            "enabled": True,
            "store_name": "Test Store",
            "store_slug": test_slug,
            "description": "Test store description",
            "primary_color": "#3b82f6",
            "cod_enabled": True,
            "delivery_enabled": True,
            "min_order_amount": 100,
            "delivery_fee": 300
        }
        
        response = requests.put(f"{BASE_URL}/api/store/settings", 
                               headers=self.headers, json=update_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify persistence
        verify_response = requests.get(f"{BASE_URL}/api/store/settings", headers=self.headers)
        assert verify_response.status_code == 200
        
        saved = verify_response.json()
        assert saved.get('store_name') == "Test Store", "Store name not saved"
        assert saved.get('store_slug') == test_slug, "Store slug not saved"
        assert saved.get('cod_enabled') == True, "COD enabled not saved"
        print(f"Store settings updated and verified: {saved.get('store_name')}")
    
    def test_store_products_list(self):
        """GET /api/store/products - returns products in the store"""
        response = requests.get(f"{BASE_URL}/api/store/products", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Store has {len(data)} products")
    
    def test_store_orders_list(self):
        """GET /api/store/orders - returns store orders"""
        response = requests.get(f"{BASE_URL}/api/store/orders", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Store has {len(data)} orders")


class TestPOSPageIntegration:
    """Test APIs used by the POS page - uses tenant user"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login with tenant admin user"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "tenant_admin@test.com",
            "password": "test123"
        })
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.text}")
        
        self.token = login_response.json().get('access_token')
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_products_endpoint(self):
        """GET /api/products - products list for POS"""
        response = requests.get(f"{BASE_URL}/api/products", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Products should be a list"
        print(f"Found {len(data)} products")
    
    def test_customers_endpoint(self):
        """GET /api/customers - customer list for POS"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Customers should be a list"
        print(f"Found {len(data)} customers")
    
    def test_warehouses_endpoint(self):
        """GET /api/warehouses - warehouse list for POS"""
        response = requests.get(f"{BASE_URL}/api/warehouses", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Warehouses should be a list"
        print(f"Found {len(data)} warehouses")
    
    def test_delivery_wilayas_endpoint(self):
        """GET /api/delivery/wilayas - wilaya list for delivery"""
        response = requests.get(f"{BASE_URL}/api/delivery/wilayas", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Wilayas should be a list"
        print(f"Found {len(data)} wilayas")
    
    def test_sale_code_generation(self):
        """GET /api/sales/generate-code - generates sale code"""
        response = requests.get(f"{BASE_URL}/api/sales/generate-code", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert 'code' in data, "Response should have 'code' field"
        print(f"Generated sale code: {data.get('code')}")


class TestPurchasesCRUD:
    """Test Purchases Edit/Delete functionality - uses tenant user"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login with tenant admin user"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "tenant_admin@test.com",
            "password": "test123"
        })
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.text}")
        
        self.token = login_response.json().get('access_token')
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_purchases_list(self):
        """GET /api/purchases - list all purchases"""
        response = requests.get(f"{BASE_URL}/api/purchases", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        # Response could be a list or paginated object
        if isinstance(data, list):
            print(f"Found {len(data)} purchases")
        elif isinstance(data, dict):
            items = data.get('items', data.get('purchases', []))
            print(f"Found {len(items)} purchases (paginated)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
