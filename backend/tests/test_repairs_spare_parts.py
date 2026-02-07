"""
Test suite for Repairs and Spare Parts APIs
Testing module: صيانة الهواتف النقالة (Mobile Phone Maintenance)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code}")
    data = response.json()
    return data.get("access_token")

@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestAuthentication:
    """Test authentication before repairs API tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        print(f"Login successful for user: {data['user'].get('email')}")


class TestRepairsAPI:
    """Test Repairs (Maintenance) API endpoints"""
    
    created_repair_id = None
    
    def test_get_repairs_stats(self, api_client):
        """Test GET /api/repairs/stats - should return repair statistics"""
        response = api_client.get(f"{BASE_URL}/api/repairs/stats")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify expected stats fields
        expected_fields = ["total", "received", "diagnosing", "in_progress", 
                          "waiting_parts", "completed", "delivered", "cancelled",
                          "today_repairs", "total_revenue", "total_advance"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"Repairs Stats: total={data['total']}, received={data['received']}, delivered={data['delivered']}")
    
    def test_get_repairs_list(self, api_client):
        """Test GET /api/repairs - should return list of repairs"""
        response = api_client.get(f"{BASE_URL}/api/repairs")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} repair tickets")
    
    def test_create_repair_ticket(self, api_client):
        """Test POST /api/repairs - create a new repair ticket"""
        ticket_number = f"TEST-REP-{os.urandom(4).hex()}"
        repair_data = {
            "ticket_number": ticket_number,
            "customer_name": "TEST_Customer",
            "customer_phone": "0555123456",
            "customer_phone2": "0666123456",
            "device_brand": "Samsung",
            "device_model": "Galaxy S23",
            "device_color": "black",
            "device_imei": "123456789012345",
            "device_password": "1234",
            "problems": ["screen_broken", "battery"],
            "problem_description": "شاشة مكسورة وبطارية ضعيفة - Test repair",
            "device_condition": "خدوش خفيفة على الظهر",
            "accessories": "شاحن فقط",
            "estimated_cost": 15000,
            "estimated_days": 3,
            "advance_payment": 5000,
            "technician_notes": "تم الاختبار بواسطة pytest",
            "status": "received"
        }
        
        response = api_client.post(f"{BASE_URL}/api/repairs", json=repair_data)
        assert response.status_code == 200, f"Failed to create repair: {response.text}"
        
        data = response.json()
        assert "id" in data, "No id in response"
        assert data["ticket_number"] == ticket_number, "Ticket number mismatch"
        assert data["customer_name"] == "TEST_Customer", "Customer name mismatch"
        assert data["device_brand"] == "Samsung", "Device brand mismatch"
        assert data["status"] == "received", "Status should be received"
        
        # Store for later tests
        TestRepairsAPI.created_repair_id = data["id"]
        print(f"Created repair ticket: {data['ticket_number']} with id: {data['id']}")
    
    def test_get_single_repair(self, api_client):
        """Test GET /api/repairs/{repair_id} - get specific repair"""
        if not TestRepairsAPI.created_repair_id:
            pytest.skip("No repair created to fetch")
        
        response = api_client.get(f"{BASE_URL}/api/repairs/{TestRepairsAPI.created_repair_id}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["id"] == TestRepairsAPI.created_repair_id, "ID mismatch"
        assert data["customer_name"] == "TEST_Customer", "Customer name mismatch"
        print(f"Retrieved repair: {data['ticket_number']}")
    
    def test_update_repair_status(self, api_client):
        """Test PUT /api/repairs/{repair_id} - update repair status"""
        if not TestRepairsAPI.created_repair_id:
            pytest.skip("No repair created to update")
        
        update_data = {
            "status": "diagnosing",
            "technician_notes": "جاري فحص الجهاز - Updated by pytest"
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/repairs/{TestRepairsAPI.created_repair_id}",
            json=update_data
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "diagnosing", "Status not updated"
        print(f"Updated repair status to: {data['status']}")
    
    def test_filter_repairs_by_status(self, api_client):
        """Test GET /api/repairs?status=diagnosing - filter by status"""
        response = api_client.get(f"{BASE_URL}/api/repairs?status=diagnosing")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        # All returned repairs should have diagnosing status
        for repair in data:
            assert repair["status"] == "diagnosing", f"Found repair with wrong status: {repair['status']}"
        print(f"Found {len(data)} repairs with status 'diagnosing'")
    
    def test_search_repairs(self, api_client):
        """Test GET /api/repairs?search=TEST - search functionality"""
        response = api_client.get(f"{BASE_URL}/api/repairs?search=TEST")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Search found {len(data)} repairs matching 'TEST'")
    
    def test_delete_repair(self, api_client):
        """Test DELETE /api/repairs/{repair_id} - delete repair ticket"""
        if not TestRepairsAPI.created_repair_id:
            pytest.skip("No repair created to delete")
        
        response = api_client.delete(f"{BASE_URL}/api/repairs/{TestRepairsAPI.created_repair_id}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "message" in data, "No message in response"
        print(f"Deleted repair: {TestRepairsAPI.created_repair_id}")
        
        # Verify deletion
        verify_response = api_client.get(f"{BASE_URL}/api/repairs/{TestRepairsAPI.created_repair_id}")
        assert verify_response.status_code == 404, "Repair should not exist after deletion"


class TestSparePartsAPI:
    """Test Spare Parts API endpoints"""
    
    created_part_id = None
    
    def test_get_spare_parts_stats(self, api_client):
        """Test GET /api/spare-parts/stats - should return statistics"""
        response = api_client.get(f"{BASE_URL}/api/spare-parts/stats")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        expected_fields = ["total", "low_stock", "total_buy_value", "total_sell_value", "categories"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"Spare Parts Stats: total={data['total']}, low_stock={data['low_stock']}")
    
    def test_get_spare_parts_list(self, api_client):
        """Test GET /api/spare-parts - should return list of spare parts"""
        response = api_client.get(f"{BASE_URL}/api/spare-parts")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} spare parts")
    
    def test_create_spare_part(self, api_client):
        """Test POST /api/spare-parts - create a new spare part"""
        part_data = {
            "name": "TEST_Screen Samsung S23",
            "name_ar": "شاشة سامسونج S23 - اختبار",
            "category": "screen",
            "compatible_brands": ["Samsung"],
            "compatible_models": "Galaxy S23, Galaxy S23+, Galaxy S23 Ultra",
            "quantity": 10,
            "buy_price": 8000,
            "sell_price": 12000,
            "min_stock": 2,
            "supplier": "Test Supplier",
            "notes": "Created by pytest"
        }
        
        response = api_client.post(f"{BASE_URL}/api/spare-parts", json=part_data)
        assert response.status_code == 200, f"Failed to create spare part: {response.text}"
        
        data = response.json()
        assert "id" in data, "No id in response"
        assert data["name"] == "TEST_Screen Samsung S23", "Name mismatch"
        assert data["category"] == "screen", "Category mismatch"
        assert data["quantity"] == 10, "Quantity mismatch"
        assert data["buy_price"] == 8000, "Buy price mismatch"
        assert data["sell_price"] == 12000, "Sell price mismatch"
        
        TestSparePartsAPI.created_part_id = data["id"]
        print(f"Created spare part: {data['name']} with id: {data['id']}")
    
    def test_get_single_spare_part(self, api_client):
        """Test GET /api/spare-parts/{part_id} - get specific spare part"""
        if not TestSparePartsAPI.created_part_id:
            pytest.skip("No spare part created to fetch")
        
        response = api_client.get(f"{BASE_URL}/api/spare-parts/{TestSparePartsAPI.created_part_id}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["id"] == TestSparePartsAPI.created_part_id, "ID mismatch"
        assert data["name"] == "TEST_Screen Samsung S23", "Name mismatch"
        print(f"Retrieved spare part: {data['name']}")
    
    def test_update_spare_part(self, api_client):
        """Test PUT /api/spare-parts/{part_id} - update spare part"""
        if not TestSparePartsAPI.created_part_id:
            pytest.skip("No spare part created to update")
        
        update_data = {
            "quantity": 15,
            "sell_price": 13000,
            "notes": "Updated by pytest"
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/spare-parts/{TestSparePartsAPI.created_part_id}",
            json=update_data
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["quantity"] == 15, "Quantity not updated"
        assert data["sell_price"] == 13000, "Sell price not updated"
        print(f"Updated spare part: quantity={data['quantity']}, sell_price={data['sell_price']}")
    
    def test_filter_spare_parts_by_category(self, api_client):
        """Test GET /api/spare-parts?category=screen - filter by category"""
        response = api_client.get(f"{BASE_URL}/api/spare-parts?category=screen")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        # All returned parts should have screen category
        for part in data:
            assert part["category"] == "screen", f"Found part with wrong category: {part['category']}"
        print(f"Found {len(data)} spare parts in 'screen' category")
    
    def test_search_spare_parts(self, api_client):
        """Test GET /api/spare-parts?search=TEST - search functionality"""
        response = api_client.get(f"{BASE_URL}/api/spare-parts?search=TEST")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Search found {len(data)} spare parts matching 'TEST'")
    
    def test_delete_spare_part(self, api_client):
        """Test DELETE /api/spare-parts/{part_id} - delete spare part"""
        if not TestSparePartsAPI.created_part_id:
            pytest.skip("No spare part created to delete")
        
        response = api_client.delete(f"{BASE_URL}/api/spare-parts/{TestSparePartsAPI.created_part_id}")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "message" in data, "No message in response"
        print(f"Deleted spare part: {TestSparePartsAPI.created_part_id}")
        
        # Verify deletion
        verify_response = api_client.get(f"{BASE_URL}/api/spare-parts/{TestSparePartsAPI.created_part_id}")
        assert verify_response.status_code == 404, "Spare part should not exist after deletion"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
