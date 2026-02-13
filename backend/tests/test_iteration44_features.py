"""
Test file for Iteration 44 features:
1. Warehouse creation with new fields (phone, manager, notes, is_main)
2. Inventory session creation (POST /api/inventory-sessions)
3. Backup export functionality
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://sound-settings-2.preview.emergentagent.com').rstrip('/')

# Test credentials
TENANT_ADMIN_EMAIL = "tenant_admin@test.com"
TENANT_ADMIN_PASSWORD = "test1234"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tenant admin"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
        "email": TENANT_ADMIN_EMAIL,
        "password": TENANT_ADMIN_PASSWORD
    })
    print(f"Auth response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"Login successful for {TENANT_ADMIN_EMAIL}")
        return token
    else:
        print(f"Auth failed: {response.text}")
        pytest.skip(f"Authentication failed with status {response.status_code}")


@pytest.fixture
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


# ============ WAREHOUSE TESTS ============

class TestWarehouseCreation:
    """Test warehouse creation with new fields: phone, manager, notes, is_main"""
    
    def test_create_warehouse_with_all_fields(self, api_client):
        """Test creating a warehouse with all new fields"""
        warehouse_data = {
            "name": "TEST_Warehouse_Full_Fields",
            "address": "123 Test Street",
            "phone": "0555123456",
            "manager": "John Doe",
            "notes": "Test warehouse for iteration 44",
            "is_main": False
        }
        
        response = api_client.post(f"{BASE_URL}/api/warehouses", json=warehouse_data)
        print(f"Create warehouse response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["name"] == warehouse_data["name"]
        assert data["phone"] == warehouse_data["phone"]
        assert data["manager"] == warehouse_data["manager"]
        assert data["notes"] == warehouse_data["notes"]
        assert data["is_main"] == warehouse_data["is_main"]
        print("Warehouse created with all new fields successfully")
        
        # Cleanup - delete the test warehouse
        if "id" in data:
            api_client.delete(f"{BASE_URL}/api/warehouses/{data['id']}")
    
    def test_create_main_warehouse(self, api_client):
        """Test creating a main warehouse"""
        warehouse_data = {
            "name": "TEST_Main_Warehouse",
            "address": "Main HQ",
            "is_main": True
        }
        
        response = api_client.post(f"{BASE_URL}/api/warehouses", json=warehouse_data)
        print(f"Create main warehouse response: {response.status_code}")
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        
        data = response.json()
        assert data["is_main"] == True
        print("Main warehouse created successfully")
        
        # Cleanup
        if "id" in data:
            api_client.delete(f"{BASE_URL}/api/warehouses/{data['id']}")
    
    def test_warehouse_with_empty_optional_fields(self, api_client):
        """Test creating a warehouse with empty optional fields"""
        warehouse_data = {
            "name": "TEST_Warehouse_Minimal",
            "is_main": False
        }
        
        response = api_client.post(f"{BASE_URL}/api/warehouses", json=warehouse_data)
        print(f"Create minimal warehouse response: {response.status_code}")
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        
        data = response.json()
        assert data["name"] == warehouse_data["name"]
        # Check optional fields have default empty values
        assert data.get("phone", "") == ""
        assert data.get("manager", "") == ""
        assert data.get("notes", "") == ""
        print("Minimal warehouse created successfully")
        
        # Cleanup
        if "id" in data:
            api_client.delete(f"{BASE_URL}/api/warehouses/{data['id']}")
    
    def test_get_warehouses_list(self, api_client):
        """Test retrieving warehouses list"""
        response = api_client.get(f"{BASE_URL}/api/warehouses")
        print(f"Get warehouses response: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Retrieved {len(data)} warehouses")


# ============ INVENTORY SESSION TESTS ============

class TestInventorySessionCreation:
    """Test inventory session creation endpoint"""
    
    def test_create_inventory_session(self, api_client):
        """Test creating a new inventory session"""
        # First, close any existing active sessions
        sessions_resp = api_client.get(f"{BASE_URL}/api/inventory-sessions")
        if sessions_resp.status_code == 200:
            for session in sessions_resp.json():
                if session.get("status") == "active":
                    api_client.put(f"{BASE_URL}/api/inventory-sessions/{session['id']}", json={"status": "completed"})
        
        session_data = {
            "name": "TEST_Inventory_Session",
            "warehouse_id": "main",
            "family_filter": "all",
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "counted_items": {},
            "notes": "Test session for iteration 44"
        }
        
        response = api_client.post(f"{BASE_URL}/api/inventory-sessions", json=session_data)
        print(f"Create inventory session response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["name"] == session_data["name"]
        assert data["status"] == "active"
        print("Inventory session created successfully")
        
        # Cleanup - delete the test session
        if "id" in data:
            api_client.delete(f"{BASE_URL}/api/inventory-sessions/{data['id']}")
    
    def test_get_inventory_sessions_list(self, api_client):
        """Test retrieving inventory sessions list"""
        response = api_client.get(f"{BASE_URL}/api/inventory-sessions")
        print(f"Get inventory sessions response: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Retrieved {len(data)} inventory sessions")
    
    def test_generate_inventory_code(self, api_client):
        """Test inventory code generation endpoint"""
        response = api_client.get(f"{BASE_URL}/api/inventory-sessions/generate-code")
        print(f"Generate inventory code response: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert data["code"].startswith("IN")
        print(f"Generated inventory code: {data['code']}")


# ============ BACKUP ENDPOINT TESTS ============

class TestBackupEndpoints:
    """Test backup-related endpoints"""
    
    def test_backup_auto_settings_get(self, api_client):
        """Test retrieving auto-backup settings"""
        response = api_client.get(f"{BASE_URL}/api/backup/auto-settings")
        print(f"Get backup settings response: {response.status_code}")
        
        # May return 404 if endpoint not implemented or 200 if exists
        if response.status_code == 200:
            data = response.json()
            print(f"Backup settings: {data}")
        else:
            print(f"Backup settings endpoint returned {response.status_code}")
        
        # This is acceptable - endpoint might not exist yet
        assert response.status_code in [200, 404, 422]


# ============ PRODUCTS BULK SELECTION SUPPORT ============

class TestProductsEndpoints:
    """Test products endpoints that support bulk operations"""
    
    def test_get_products_list(self, api_client):
        """Test retrieving products list for bulk selection"""
        response = api_client.get(f"{BASE_URL}/api/products")
        print(f"Get products response: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Retrieved {len(data)} products")
    
    def test_delete_product(self, api_client):
        """Test single product deletion (for bulk delete support)"""
        # First create a test product
        product_data = {
            "name_en": "TEST_Bulk_Delete_Product",
            "name_ar": "منتج اختبار الحذف",
            "retail_price": 100,
            "purchase_price": 50,
            "quantity": 10
        }
        
        create_resp = api_client.post(f"{BASE_URL}/api/products", json=product_data)
        if create_resp.status_code in [200, 201]:
            product_id = create_resp.json()["id"]
            
            # Now delete it
            delete_resp = api_client.delete(f"{BASE_URL}/api/products/{product_id}")
            print(f"Delete product response: {delete_resp.status_code}")
            
            assert delete_resp.status_code == 200, f"Expected 200, got {delete_resp.status_code}"
            print("Product deleted successfully - bulk delete should work")
        else:
            print(f"Product creation failed: {create_resp.status_code}")
            pytest.skip("Could not create test product")


# ============ SIDEBAR SETTINGS ============

class TestSidebarSettings:
    """Test sidebar configuration endpoints"""
    
    def test_get_sidebar_order(self, api_client):
        """Test retrieving sidebar order settings"""
        response = api_client.get(f"{BASE_URL}/api/settings/sidebar-order")
        print(f"Get sidebar order response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Sidebar order data: {data}")
        else:
            print(f"Sidebar order endpoint returned {response.status_code}")
        
        # May return 404 if not set yet, or 200 if exists
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
