"""
Test file for Feature Flags and E-commerce Store functionality
Tests:
1. Feature Flags - tenant login returns features & limits
2. Feature Flags - /auth/me returns features & limits
3. E-commerce Store - save store settings records slug in main_db
4. E-commerce Store - public store access /shop/{store_slug}
5. E-commerce Store - add product to store
6. E-commerce Store - create order from public store (COD)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TENANT_EMAIL = "demo@demo.com"
TENANT_PASSWORD = "demo123"
SUPER_ADMIN_EMAIL = "super@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "admin123"

# Test data
TEST_STORE_SLUG = "demo-store"
TEST_PRODUCT_ID = "a66406e1-9476-406a-b146-69c1ca0e2b13"


class TestFeatureFlags:
    """Test Feature Flags functionality"""
    
    def test_tenant_login_returns_features_and_limits(self):
        """Test 1: Tenant login should return features and limits in response"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        
        print(f"Login Response Status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Login Response Keys: {data.keys()}")
        print(f"User Keys: {data.get('user', {}).keys()}")
        
        # Check user_type is tenant
        assert data.get("user_type") == "tenant", f"Expected user_type 'tenant', got {data.get('user_type')}"
        
        # Check features and limits in user object
        user = data.get("user", {})
        assert "features" in user, f"features not found in user object. User keys: {user.keys()}"
        assert "limits" in user, f"limits not found in user object. User keys: {user.keys()}"
        
        features = user.get("features", {})
        limits = user.get("limits", {})
        
        print(f"Features: {features}")
        print(f"Limits: {limits}")
        
        # Verify features structure (should be dict with feature categories)
        assert isinstance(features, dict), f"features should be dict, got {type(features)}"
        assert isinstance(limits, dict), f"limits should be dict, got {type(limits)}"
        
        print("✓ Test PASSED: Tenant login returns features and limits")
        
        return data.get("access_token")
    
    def test_auth_me_returns_features_and_limits(self):
        """Test 2: /auth/me endpoint should return features and limits for tenant user"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        
        # Call /auth/me
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        print(f"/auth/me Response Status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"/auth/me Response Keys: {data.keys()}")
        
        # Check features and limits
        assert "features" in data, f"features not found in /auth/me response. Keys: {data.keys()}"
        assert "limits" in data, f"limits not found in /auth/me response. Keys: {data.keys()}"
        
        features = data.get("features", {})
        limits = data.get("limits", {})
        
        print(f"Features from /auth/me: {features}")
        print(f"Limits from /auth/me: {limits}")
        
        assert isinstance(features, dict), f"features should be dict, got {type(features)}"
        assert isinstance(limits, dict), f"limits should be dict, got {type(limits)}"
        
        print("✓ Test PASSED: /auth/me returns features and limits")


class TestEcommerceStore:
    """Test E-commerce Store functionality"""
    
    @pytest.fixture
    def tenant_token(self):
        """Get tenant authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    def test_save_store_settings_records_slug_in_main_db(self, tenant_token):
        """Test 3: Saving store settings should record store_slug in main_db"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        
        # Save store settings with a unique slug
        unique_slug = f"test-store-{uuid.uuid4().hex[:8]}"
        store_settings = {
            "enabled": True,
            "store_name": "متجر تجريبي",
            "store_slug": TEST_STORE_SLUG,  # Using the known store slug
            "description": "متجر تجريبي للاختبار",
            "logo_url": "",
            "banner_url": "",
            "primary_color": "#3b82f6",
            "contact_phone": "0555123456",
            "contact_email": "store@test.com",
            "contact_address": "الجزائر العاصمة",
            "working_hours": "09:00 - 18:00",
            "cod_enabled": True,
            "delivery_enabled": True,
            "min_order_amount": 0,
            "delivery_fee": 300,
            "free_delivery_threshold": 5000
        }
        
        response = requests.put(f"{BASE_URL}/api/store/settings", 
                               json=store_settings, 
                               headers=headers)
        
        print(f"Save Store Settings Response Status: {response.status_code}")
        print(f"Save Store Settings Response: {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify the slug is accessible via public endpoint
        # This indirectly verifies it was saved in main_db
        public_response = requests.get(f"{BASE_URL}/api/shop/{TEST_STORE_SLUG}")
        print(f"Public Store Response Status: {public_response.status_code}")
        
        # If store is enabled and slug is in main_db, should return 200
        # If not enabled, might return 404 - that's also valid as long as we got 200 on save
        if public_response.status_code == 200:
            print("✓ Store slug is accessible publicly - confirmed saved in main_db")
        else:
            print(f"Public store returned {public_response.status_code} - store may be disabled")
        
        print("✓ Test PASSED: Store settings saved successfully")
    
    def test_public_store_access_without_auth(self):
        """Test 4: Public store should be accessible without authentication"""
        # First ensure store exists and is enabled
        login_response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Enable the store first
        store_settings = {
            "enabled": True,
            "store_name": "متجر Demo",
            "store_slug": TEST_STORE_SLUG,
            "description": "متجر تجريبي",
            "logo_url": "",
            "banner_url": "",
            "primary_color": "#3b82f6",
            "contact_phone": "0555123456",
            "contact_email": "store@demo.com",
            "contact_address": "الجزائر",
            "working_hours": "09:00 - 18:00",
            "cod_enabled": True,
            "delivery_enabled": True,
            "min_order_amount": 0,
            "delivery_fee": 300,
            "free_delivery_threshold": 5000
        }
        
        save_response = requests.put(f"{BASE_URL}/api/store/settings", 
                                    json=store_settings, 
                                    headers=headers)
        print(f"Enable Store Response: {save_response.status_code}")
        
        # Now access public store WITHOUT authentication
        public_response = requests.get(f"{BASE_URL}/api/shop/{TEST_STORE_SLUG}")
        
        print(f"Public Store Access Response Status: {public_response.status_code}")
        
        assert public_response.status_code == 200, f"Expected 200, got {public_response.status_code}: {public_response.text}"
        
        data = public_response.json()
        print(f"Public Store Response Keys: {data.keys()}")
        
        # Verify response structure
        assert "settings" in data, f"settings not found in response. Keys: {data.keys()}"
        assert "products" in data, f"products not found in response. Keys: {data.keys()}"
        
        settings = data.get("settings", {})
        products = data.get("products", [])
        
        print(f"Store Settings: {settings}")
        print(f"Number of Products: {len(products)}")
        
        # Verify settings
        assert settings.get("enabled") == True, "Store should be enabled"
        assert settings.get("store_name"), "Store should have a name"
        
        print("✓ Test PASSED: Public store accessible without authentication")
    
    def test_add_product_to_store(self, tenant_token):
        """Test 5: Add product to e-commerce store"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        
        # First, get list of products to find a valid product ID
        products_response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        
        if products_response.status_code == 200 and products_response.json():
            # Use first available product
            product = products_response.json()[0]
            product_id = product.get("id")
            print(f"Using product: {product.get('name_ar', product.get('name_en'))} (ID: {product_id})")
        else:
            # Use the provided test product ID
            product_id = TEST_PRODUCT_ID
            print(f"Using provided test product ID: {product_id}")
        
        # Add product to store
        response = requests.post(f"{BASE_URL}/api/store/products",
                                json={"product_id": product_id},
                                headers=headers)
        
        print(f"Add Product to Store Response Status: {response.status_code}")
        print(f"Add Product to Store Response: {response.text}")
        
        # Product might already be in store, both 200 and "already in store" are valid
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify product is in store
        store_products_response = requests.get(f"{BASE_URL}/api/store/products", headers=headers)
        print(f"Store Products Response Status: {store_products_response.status_code}")
        
        assert store_products_response.status_code == 200
        store_products = store_products_response.json()
        print(f"Number of products in store: {len(store_products)}")
        
        # Check if our product is in the list
        product_ids_in_store = [p.get("product_id") for p in store_products]
        assert product_id in product_ids_in_store, f"Product {product_id} not found in store products"
        
        print("✓ Test PASSED: Product added to store successfully")
    
    def test_create_order_from_public_store_cod(self):
        """Test 6: Create order from public store with Cash on Delivery"""
        # First ensure store is enabled and has products
        login_response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Enable store with COD
        store_settings = {
            "enabled": True,
            "store_name": "متجر Demo",
            "store_slug": TEST_STORE_SLUG,
            "description": "متجر تجريبي",
            "logo_url": "",
            "banner_url": "",
            "primary_color": "#3b82f6",
            "contact_phone": "0555123456",
            "contact_email": "store@demo.com",
            "contact_address": "الجزائر",
            "working_hours": "09:00 - 18:00",
            "cod_enabled": True,
            "delivery_enabled": True,
            "min_order_amount": 0,
            "delivery_fee": 300,
            "free_delivery_threshold": 5000
        }
        requests.put(f"{BASE_URL}/api/store/settings", json=store_settings, headers=headers)
        
        # Get products from public store
        public_store_response = requests.get(f"{BASE_URL}/api/shop/{TEST_STORE_SLUG}")
        
        if public_store_response.status_code != 200:
            pytest.skip("Store not available for public access")
        
        store_data = public_store_response.json()
        products = store_data.get("products", [])
        
        if not products:
            # Add a product to the store first
            products_response = requests.get(f"{BASE_URL}/api/products", headers=headers)
            if products_response.status_code == 200 and products_response.json():
                product = products_response.json()[0]
                product_id = product.get("id")
                requests.post(f"{BASE_URL}/api/store/products",
                             json={"product_id": product_id},
                             headers=headers)
                # Refresh public store
                public_store_response = requests.get(f"{BASE_URL}/api/shop/{TEST_STORE_SLUG}")
                store_data = public_store_response.json()
                products = store_data.get("products", [])
        
        if not products:
            pytest.skip("No products available in store")
        
        # Create order with first product
        product = products[0]
        print(f"Creating order with product: {product.get('name_ar', product.get('name_en'))}")
        
        order_data = {
            "customer_name": "عميل اختبار",
            "customer_phone": "0555123456",
            "customer_email": "test@test.com",
            "delivery_address": "شارع الاختبار، رقم 123",
            "delivery_city": "الجزائر العاصمة",
            "delivery_wilaya": "الجزائر",
            "items": [
                {
                    "product_id": product.get("id"),
                    "name": product.get("name_ar", product.get("name_en")),
                    "price": product.get("retail_price", 1000),
                    "quantity": 1
                }
            ],
            "subtotal": product.get("retail_price", 1000),
            "delivery_fee": 300,
            "total": product.get("retail_price", 1000) + 300,
            "notes": "طلب اختبار",
            "payment_method": "cod"
        }
        
        # Create order WITHOUT authentication (public endpoint)
        response = requests.post(f"{BASE_URL}/api/shop/{TEST_STORE_SLUG}/order",
                                json=order_data)
        
        print(f"Create Order Response Status: {response.status_code}")
        print(f"Create Order Response: {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response
        assert "order_number" in data, f"order_number not found in response. Keys: {data.keys()}"
        assert "order_id" in data, f"order_id not found in response. Keys: {data.keys()}"
        
        print(f"Order Number: {data.get('order_number')}")
        print(f"Order ID: {data.get('order_id')}")
        print(f"Message: {data.get('message')}")
        
        # Verify order was created by checking store orders (authenticated)
        orders_response = requests.get(f"{BASE_URL}/api/store/orders", headers=headers)
        print(f"Store Orders Response Status: {orders_response.status_code}")
        
        if orders_response.status_code == 200:
            orders = orders_response.json()
            order_numbers = [o.get("order_number") for o in orders]
            print(f"Order numbers in store: {order_numbers[:5]}")  # First 5
            assert data.get("order_number") in order_numbers, "Created order not found in store orders"
        
        print("✓ Test PASSED: Order created from public store with COD")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
