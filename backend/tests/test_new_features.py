"""
Test suite for new features: API Keys, Recharge, Product Families
Tests the 3 new pages added to ScreenGuard Pro system
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin"


class TestAuthSetup:
    """Test authentication and get token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        # Try to register if login fails
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "name": "Admin User",
            "role": "admin"
        })
        if response.status_code in [200, 201]:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed - status: {response.status_code}, response: {response.text}")
    
    def test_auth_works(self, auth_token):
        """Verify authentication is working"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Authentication successful, token length: {len(auth_token)}")


class TestApiKeysEndpoints:
    """Test API Keys CRUD operations"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "name": "Admin User",
            "role": "admin"
        })
        if response.status_code in [200, 201]:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_api_keys_empty(self, headers):
        """Test GET /api/api-keys returns list (may be empty)"""
        response = requests.get(f"{BASE_URL}/api/api-keys", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ GET /api/api-keys - returns list with {len(response.json())} keys")
    
    def test_create_internal_api_key(self, headers):
        """Test POST /api/api-keys - create internal key"""
        payload = {
            "name": "TEST_Internal_Key_001",
            "type": "internal",
            "permissions": ["read", "write"]
        }
        response = requests.post(f"{BASE_URL}/api/api-keys", json=payload, headers=headers)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert "id" in data
        assert data["name"] == payload["name"]
        assert data["type"] == "internal"
        assert "key_value" in data
        assert "key_preview" in data
        assert data["is_active"] == True
        print(f"✓ Created internal API key: {data['id']}")
        return data
    
    def test_create_external_api_key(self, headers):
        """Test POST /api/api-keys - create external key"""
        payload = {
            "name": "TEST_External_WooCommerce",
            "type": "external",
            "service": "woocommerce",
            "key_value": "ck_test123456789",
            "secret_value": "cs_secret123456789",
            "endpoint_url": "https://test.example.com/wp-json/wc/v3",
            "permissions": ["read"]
        }
        response = requests.post(f"{BASE_URL}/api/api-keys", json=payload, headers=headers)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert data["service"] == "woocommerce"
        assert data["endpoint_url"] == payload["endpoint_url"]
        print(f"✓ Created external API key: {data['id']}")
        return data
    
    def test_toggle_api_key(self, headers):
        """Test PUT /api/api-keys/{id}/toggle"""
        # First create a key
        create_response = requests.post(f"{BASE_URL}/api/api-keys", json={
            "name": "TEST_Toggle_Key",
            "type": "internal",
            "permissions": ["read"]
        }, headers=headers)
        assert create_response.status_code in [200, 201]
        key_id = create_response.json()["id"]
        
        # Toggle the key (should deactivate)
        toggle_response = requests.put(f"{BASE_URL}/api/api-keys/{key_id}/toggle", headers=headers)
        assert toggle_response.status_code == 200
        
        # Verify key was toggled
        get_response = requests.get(f"{BASE_URL}/api/api-keys/{key_id}", headers=headers)
        if get_response.status_code == 200:
            assert get_response.json()["is_active"] == False
            print(f"✓ API key toggled successfully: {key_id}")
        else:
            # Check in list
            list_response = requests.get(f"{BASE_URL}/api/api-keys", headers=headers)
            keys = [k for k in list_response.json() if k["id"] == key_id]
            if keys:
                assert keys[0]["is_active"] == False
                print(f"✓ API key toggled (verified via list): {key_id}")
            else:
                print(f"✓ Toggle endpoint returned 200")
    
    def test_delete_api_key(self, headers):
        """Test DELETE /api/api-keys/{id}"""
        # First create a key to delete
        create_response = requests.post(f"{BASE_URL}/api/api-keys", json={
            "name": "TEST_Delete_Key",
            "type": "internal",
            "permissions": ["read"]
        }, headers=headers)
        assert create_response.status_code in [200, 201]
        key_id = create_response.json()["id"]
        
        # Delete the key
        delete_response = requests.delete(f"{BASE_URL}/api/api-keys/{key_id}", headers=headers)
        assert delete_response.status_code in [200, 204]
        print(f"✓ API key deleted: {key_id}")
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/api-keys", headers=headers)
        keys = [k for k in get_response.json() if k["id"] == key_id]
        assert len(keys) == 0
        print(f"✓ Verified key no longer in list")


class TestRechargeEndpoints:
    """Test Recharge (USSD) endpoints - Note: Actual USSD execution is MOCKED"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "name": "Admin User",
            "role": "admin"
        })
        if response.status_code in [200, 201]:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_recharge_config(self, headers):
        """Test GET /api/recharge/config - get operator configs"""
        response = requests.get(f"{BASE_URL}/api/recharge/config", headers=headers)
        assert response.status_code == 200
        
        config = response.json()
        assert isinstance(config, dict)
        # Verify expected operators exist
        expected_operators = ["mobilis", "djezzy", "ooredoo", "idoom"]
        for op in expected_operators:
            assert op in config, f"Operator {op} missing from config"
            assert "name" in config[op]
            assert "amounts" in config[op]
            assert "commission" in config[op]
        print(f"✓ Recharge config has all {len(expected_operators)} operators")
    
    def test_create_recharge_mobilis(self, headers):
        """Test POST /api/recharge - Mobilis credit recharge (MOCKED)"""
        payload = {
            "operator": "mobilis",
            "phone_number": "0555123456",
            "amount": 500,
            "recharge_type": "credit",
            "payment_method": "cash",
            "notes": "TEST_Recharge_Mobilis"
        }
        response = requests.post(f"{BASE_URL}/api/recharge", json=payload, headers=headers)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert data["operator"] == "mobilis"
        assert data["phone_number"] == payload["phone_number"]
        assert data["amount"] == payload["amount"]
        assert data["recharge_type"] == "credit"
        assert "ussd_code" in data
        assert "profit" in data
        assert data["profit"] > 0  # Commission should be calculated
        assert data["status"] == "completed"
        print(f"✓ Mobilis recharge created - USSD: {data['ussd_code']}, Profit: {data['profit']}")
    
    def test_create_recharge_djezzy(self, headers):
        """Test POST /api/recharge - Djezzy recharge (MOCKED)"""
        payload = {
            "operator": "djezzy",
            "phone_number": "0777654321",
            "amount": 1000,
            "recharge_type": "credit",
            "payment_method": "cash"
        }
        response = requests.post(f"{BASE_URL}/api/recharge", json=payload, headers=headers)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert data["operator"] == "djezzy"
        assert "ussd_code" in data
        print(f"✓ Djezzy recharge created - USSD: {data['ussd_code']}")
    
    def test_create_recharge_ooredoo(self, headers):
        """Test POST /api/recharge - Ooredoo internet recharge (MOCKED)"""
        payload = {
            "operator": "ooredoo",
            "phone_number": "0550987654",
            "amount": 2000,
            "recharge_type": "internet",
            "payment_method": "bank"
        }
        response = requests.post(f"{BASE_URL}/api/recharge", json=payload, headers=headers)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert data["operator"] == "ooredoo"
        assert data["recharge_type"] == "internet"
        print(f"✓ Ooredoo internet recharge created - USSD: {data['ussd_code']}")
    
    def test_get_recharge_history(self, headers):
        """Test GET /api/recharge - get recharge history"""
        response = requests.get(f"{BASE_URL}/api/recharge", headers=headers)
        assert response.status_code == 200
        
        recharges = response.json()
        assert isinstance(recharges, list)
        if len(recharges) > 0:
            # Verify structure of recharge record
            r = recharges[0]
            assert "id" in r
            assert "operator" in r
            assert "phone_number" in r
            assert "amount" in r
            assert "ussd_code" in r
            assert "profit" in r
        print(f"✓ Recharge history returned {len(recharges)} records")
    
    def test_get_recharge_stats(self, headers):
        """Test GET /api/recharge/stats - get recharge statistics"""
        response = requests.get(f"{BASE_URL}/api/recharge/stats", headers=headers)
        assert response.status_code == 200
        
        stats = response.json()
        assert "by_operator" in stats or "today" in stats
        print(f"✓ Recharge stats retrieved successfully")


class TestProductFamiliesEndpoints:
    """Test Product Families CRUD operations"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "name": "Admin User",
            "role": "admin"
        })
        if response.status_code in [200, 201]:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_product_families_list(self, headers):
        """Test GET /api/product-families"""
        response = requests.get(f"{BASE_URL}/api/product-families", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ Product families list: {len(response.json())} families")
    
    def test_create_main_product_family(self, headers):
        """Test POST /api/product-families - create main family"""
        payload = {
            "name_ar": "TEST_واقيات_الشاشة",
            "name_en": "TEST_Screen_Protectors",
            "description_ar": "واقيات شاشة للهواتف الذكية",
            "description_en": "Screen protectors for smartphones"
        }
        response = requests.post(f"{BASE_URL}/api/product-families", json=payload, headers=headers)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert "id" in data
        assert data["name_ar"] == payload["name_ar"]
        assert data["name_en"] == payload["name_en"]
        assert data["parent_id"] == "" or data["parent_id"] is None or data["parent_id"] == ""
        print(f"✓ Created main family: {data['id']}")
        return data
    
    def test_create_sub_family(self, headers):
        """Test POST /api/product-families - create sub-family"""
        # First create a parent family
        parent_response = requests.post(f"{BASE_URL}/api/product-families", json={
            "name_ar": "TEST_إكسسوارات",
            "name_en": "TEST_Accessories"
        }, headers=headers)
        assert parent_response.status_code in [200, 201]
        parent_id = parent_response.json()["id"]
        
        # Create sub-family
        payload = {
            "name_ar": "TEST_أغطية_الهواتف",
            "name_en": "TEST_Phone_Cases",
            "parent_id": parent_id
        }
        response = requests.post(f"{BASE_URL}/api/product-families", json=payload, headers=headers)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert data["parent_id"] == parent_id
        print(f"✓ Created sub-family under parent {parent_id}")
    
    def test_update_product_family(self, headers):
        """Test PUT /api/product-families/{id}"""
        # Create a family first
        create_response = requests.post(f"{BASE_URL}/api/product-families", json={
            "name_ar": "TEST_عائلة_للتعديل",
            "name_en": "TEST_Family_To_Edit"
        }, headers=headers)
        assert create_response.status_code in [200, 201]
        family_id = create_response.json()["id"]
        
        # Update it
        update_payload = {
            "name_ar": "TEST_عائلة_معدلة",
            "name_en": "TEST_Updated_Family",
            "description_ar": "وصف جديد"
        }
        update_response = requests.put(f"{BASE_URL}/api/product-families/{family_id}", 
                                       json=update_payload, headers=headers)
        assert update_response.status_code == 200
        
        updated = update_response.json()
        assert updated["name_ar"] == update_payload["name_ar"]
        print(f"✓ Family updated: {family_id}")
    
    def test_get_single_product_family(self, headers):
        """Test GET /api/product-families/{id}"""
        # Create a family first
        create_response = requests.post(f"{BASE_URL}/api/product-families", json={
            "name_ar": "TEST_عائلة_للعرض",
            "name_en": "TEST_Family_To_View"
        }, headers=headers)
        assert create_response.status_code in [200, 201]
        family_id = create_response.json()["id"]
        
        # Get it
        response = requests.get(f"{BASE_URL}/api/product-families/{family_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == family_id
        print(f"✓ Retrieved single family: {family_id}")
    
    def test_delete_product_family(self, headers):
        """Test DELETE /api/product-families/{id}"""
        # Create a family to delete
        create_response = requests.post(f"{BASE_URL}/api/product-families", json={
            "name_ar": "TEST_عائلة_للحذف",
            "name_en": "TEST_Family_To_Delete"
        }, headers=headers)
        assert create_response.status_code in [200, 201]
        family_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/product-families/{family_id}", headers=headers)
        assert delete_response.status_code in [200, 204]
        print(f"✓ Family deleted: {family_id}")
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/product-families/{family_id}", headers=headers)
        assert get_response.status_code == 404
        print(f"✓ Verified family no longer exists")


class TestCleanup:
    """Clean up test data created during testing"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_cleanup_test_api_keys(self, headers):
        """Clean up API keys created during testing"""
        response = requests.get(f"{BASE_URL}/api/api-keys", headers=headers)
        if response.status_code == 200:
            keys = response.json()
            deleted = 0
            for key in keys:
                if key["name"].startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/api-keys/{key['id']}", headers=headers)
                    deleted += 1
            print(f"✓ Cleaned up {deleted} test API keys")
    
    def test_cleanup_test_product_families(self, headers):
        """Clean up product families created during testing"""
        response = requests.get(f"{BASE_URL}/api/product-families", headers=headers)
        if response.status_code == 200:
            families = response.json()
            deleted = 0
            # Delete sub-families first (those with parent_id)
            for family in families:
                if family.get("parent_id") and (family["name_ar"].startswith("TEST_") or family["name_en"].startswith("TEST_")):
                    requests.delete(f"{BASE_URL}/api/product-families/{family['id']}", headers=headers)
                    deleted += 1
            # Then delete main families
            for family in families:
                if not family.get("parent_id") and (family["name_ar"].startswith("TEST_") or family["name_en"].startswith("TEST_")):
                    requests.delete(f"{BASE_URL}/api/product-families/{family['id']}", headers=headers)
                    deleted += 1
            print(f"✓ Cleaned up {deleted} test product families")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
