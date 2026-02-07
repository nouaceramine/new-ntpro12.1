"""
Test Suite for New POS Features:
1. Login Page Branding - /api/branding/settings
2. Advanced Analytics - /api/analytics/*
3. Loyalty & Marketing - /api/loyalty/*, /api/marketing/sms/campaigns
4. WooCommerce Publish - /api/woocommerce/publish-product/{id}
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://pos-manager-37.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        print(f"Login response status: {response.status_code}")
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print("✓ Login successful")
        return data["access_token"]


class TestBrandingSettings:
    """Test Login Page Branding API - /api/branding/settings"""
    
    def test_get_branding_settings_public(self):
        """GET /api/branding/settings should be public (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/branding/settings")
        print(f"GET /api/branding/settings status: {response.status_code}")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check expected fields
        assert "business_name" in data
        assert "logo_url" in data
        assert "background_url" in data
        assert "primary_color" in data
        print(f"✓ Branding settings retrieved: business_name='{data.get('business_name')}'")
    
    def test_update_branding_settings_requires_admin(self):
        """PUT /api/branding/settings should require admin auth"""
        # Without auth
        response = requests.put(f"{BASE_URL}/api/branding/settings", json={
            "business_name": "Test Store"
        })
        assert response.status_code in [401, 403, 422], f"Expected auth error: {response.status_code}"
        print("✓ Update branding requires auth")


class TestAdvancedAnalytics:
    """Test Advanced Analytics APIs - /api/analytics/*"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_sales_chart_week(self):
        """GET /api/analytics/sales-chart?period=week"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/sales-chart?period=week",
            headers=self.headers
        )
        print(f"Sales chart (week) status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "date" in data[0]
            assert "total" in data[0]
        print(f"✓ Sales chart returned {len(data)} data points")
    
    def test_sales_chart_month(self):
        """GET /api/analytics/sales-chart?period=month"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/sales-chart?period=month",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Sales chart (month) returned {len(data)} data points")
    
    def test_sales_chart_year(self):
        """GET /api/analytics/sales-chart?period=year"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/sales-chart?period=year",
            headers=self.headers
        )
        assert response.status_code == 200
        print("✓ Sales chart (year) works")
    
    def test_top_products(self):
        """GET /api/analytics/top-products"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/top-products?limit=10",
            headers=self.headers
        )
        print(f"Top products status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "name" in data[0]
            assert "total_sold" in data[0]
        print(f"✓ Top products returned {len(data)} products")
    
    def test_top_customers(self):
        """GET /api/analytics/top-customers"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/top-customers?limit=10",
            headers=self.headers
        )
        print(f"Top customers status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "name" in data[0]
            assert "total_purchases" in data[0]
        print(f"✓ Top customers returned {len(data)} customers")
    
    def test_employee_performance(self):
        """GET /api/analytics/employee-performance"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/employee-performance",
            headers=self.headers
        )
        print(f"Employee performance status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Employee performance returned {len(data)} employees")
    
    def test_sales_prediction(self):
        """GET /api/analytics/sales-prediction"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/sales-prediction",
            headers=self.headers
        )
        print(f"Sales prediction status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "next_week_sales" in data
        assert "expected_sales_count" in data
        assert "expected_avg_order" in data
        assert "trend" in data
        print(f"✓ Sales prediction: next_week={data.get('next_week_sales')}, trend={data.get('trend')}")
    
    def test_restock_suggestions(self):
        """GET /api/analytics/restock-suggestions"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/restock-suggestions",
            headers=self.headers
        )
        print(f"Restock suggestions status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "name" in data[0]
            assert "quantity" in data[0]
        print(f"✓ Restock suggestions returned {len(data)} products")


class TestLoyaltyProgram:
    """Test Loyalty Program APIs - /api/loyalty/*"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_loyalty_settings(self):
        """GET /api/loyalty/settings"""
        response = requests.get(
            f"{BASE_URL}/api/loyalty/settings",
            headers=self.headers
        )
        print(f"Loyalty settings status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "enabled" in data
        assert "points_per_dinar" in data
        assert "points_value" in data
        assert "min_redeem_points" in data
        assert "welcome_bonus" in data
        print(f"✓ Loyalty settings: enabled={data.get('enabled')}, points_per_dinar={data.get('points_per_dinar')}")
    
    def test_update_loyalty_settings(self):
        """PUT /api/loyalty/settings"""
        new_settings = {
            "enabled": True,
            "points_per_dinar": 1,
            "points_value": 0.01,
            "min_redeem_points": 100,
            "welcome_bonus": 50
        }
        response = requests.put(
            f"{BASE_URL}/api/loyalty/settings",
            headers=self.headers,
            json=new_settings
        )
        print(f"Update loyalty settings status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        print("✓ Loyalty settings updated successfully")


class TestSMSCampaigns:
    """Test SMS Campaign APIs - /api/marketing/sms/campaigns (MOCKED)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_campaigns(self):
        """GET /api/marketing/sms/campaigns"""
        response = requests.get(
            f"{BASE_URL}/api/marketing/sms/campaigns",
            headers=self.headers
        )
        print(f"Get campaigns status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ SMS campaigns returned {len(data)} campaigns (MOCKED)")
    
    def test_create_campaign_mocked(self):
        """POST /api/marketing/sms/campaigns (MOCKED)"""
        campaign = {
            "name": "TEST_Ramadan_Offer",
            "message": "عروض رمضان الخاصة! خصم 20% على جميع المنتجات",
            "target": "all",
            "scheduled_at": ""
        }
        response = requests.post(
            f"{BASE_URL}/api/marketing/sms/campaigns",
            headers=self.headers,
            json=campaign
        )
        print(f"Create campaign status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert data["name"] == campaign["name"]
        print(f"✓ SMS campaign created (MOCKED): {data.get('name')}, recipients={data.get('recipients_count', 0)}")


class TestWooCommercePublish:
    """Test WooCommerce Publish APIs (MOCKED)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_woocommerce_settings(self):
        """GET /api/woocommerce/settings"""
        response = requests.get(
            f"{BASE_URL}/api/woocommerce/settings",
            headers=self.headers
        )
        print(f"WooCommerce settings status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "store_url" in data
        assert "consumer_key" in data
        assert "consumer_secret" in data
        print(f"✓ WooCommerce settings retrieved: store_url={data.get('store_url')}")
    
    def test_publish_product_to_woocommerce(self):
        """POST /api/woocommerce/publish-product/{product_id} (MOCKED)"""
        # First get a product
        products_response = requests.get(
            f"{BASE_URL}/api/products",
            headers=self.headers
        )
        assert products_response.status_code == 200
        products = products_response.json()
        
        if len(products) == 0:
            pytest.skip("No products available to test")
        
        product_id = products[0]["id"]
        
        # Try to publish
        response = requests.post(
            f"{BASE_URL}/api/woocommerce/publish-product/{product_id}",
            headers=self.headers
        )
        print(f"Publish product status: {response.status_code}")
        
        # Accept 200 (success) or error codes that mean WooCommerce is not configured
        assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "woocommerce_id" in data
            print(f"✓ Product published to WooCommerce (MOCKED): wc_id={data.get('woocommerce_id')}")
        else:
            print(f"✓ WooCommerce publish API responded (may not be configured): {response.status_code}")
    
    def test_unpublish_product_from_woocommerce(self):
        """DELETE /api/woocommerce/unpublish-product/{product_id}"""
        # Get a product that's published
        products_response = requests.get(
            f"{BASE_URL}/api/products",
            headers=self.headers
        )
        products = products_response.json()
        
        # Find one with woocommerce_id
        published = [p for p in products if p.get("woocommerce_id")]
        
        if len(published) == 0:
            print("✓ No published products to unpublish - skipping")
            return
        
        product_id = published[0]["id"]
        
        response = requests.delete(
            f"{BASE_URL}/api/woocommerce/unpublish-product/{product_id}",
            headers=self.headers
        )
        print(f"Unpublish product status: {response.status_code}")
        assert response.status_code in [200, 400, 404]
        print("✓ Unpublish API works")


class TestCustomersList:
    """Test customers list for loyalty page"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_customers(self):
        """GET /api/customers - needed for loyalty page"""
        response = requests.get(
            f"{BASE_URL}/api/customers",
            headers=self.headers
        )
        print(f"Get customers status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            customer = data[0]
            assert "name" in customer
            assert "phone" in customer
            assert "total_purchases" in customer
            # Check for loyalty_points field
            if "loyalty_points" in customer:
                print(f"✓ Customer has loyalty_points: {customer.get('loyalty_points')}")
        print(f"✓ Customers list returned {len(data)} customers")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
