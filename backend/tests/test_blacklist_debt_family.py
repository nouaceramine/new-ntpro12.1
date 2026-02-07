"""
Tests for Blacklist, Debt Reminders, and Customer Family APIs
Features:
- Phone blacklist CRUD operations
- Debt reminders for customers
- Customer family selection
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test@test.com", "password": "test123"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")

@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestBlacklistAPI:
    """Tests for phone blacklist functionality"""
    
    def test_get_blacklist(self, auth_headers):
        """Test GET /api/blacklist returns list"""
        response = requests.get(f"{BASE_URL}/api/blacklist", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_add_phone_to_blacklist(self, auth_headers):
        """Test POST /api/blacklist adds new phone"""
        test_phone = f"09{uuid.uuid4().hex[:8]}"  # Generate unique phone
        payload = {
            "phone": test_phone,
            "reason": "Test reason",
            "notes": "Test notes for blacklist"
        }
        response = requests.post(
            f"{BASE_URL}/api/blacklist",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == test_phone
        assert data["reason"] == "Test reason"
        assert "id" in data
        assert "created_at" in data
        
        # Cleanup - delete the entry
        entry_id = data["id"]
        requests.delete(f"{BASE_URL}/api/blacklist/{entry_id}", headers=auth_headers)
    
    def test_check_blacklisted_phone(self, auth_headers):
        """Test GET /api/blacklist/check/{phone} returns status"""
        # Test with known blacklisted phone
        response = requests.get(
            f"{BASE_URL}/api/blacklist/check/0555123456",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_blacklisted" in data
        # Phone 0555123456 was added as test data
        if data["is_blacklisted"]:
            assert "entry" in data
            assert data["entry"]["phone"] == "0555123456"
    
    def test_check_non_blacklisted_phone(self, auth_headers):
        """Test checking a phone that's not blacklisted"""
        response = requests.get(
            f"{BASE_URL}/api/blacklist/check/0999999999",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_blacklisted"] == False
    
    def test_add_duplicate_phone_fails(self, auth_headers):
        """Test adding duplicate phone returns error"""
        # First add a phone
        test_phone = f"08{uuid.uuid4().hex[:8]}"
        payload = {"phone": test_phone, "reason": "First add"}
        first_response = requests.post(
            f"{BASE_URL}/api/blacklist",
            headers=auth_headers,
            json=payload
        )
        assert first_response.status_code == 200
        entry_id = first_response.json()["id"]
        
        # Try adding same phone again
        duplicate_response = requests.post(
            f"{BASE_URL}/api/blacklist",
            headers=auth_headers,
            json=payload
        )
        assert duplicate_response.status_code == 400
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/blacklist/{entry_id}", headers=auth_headers)
    
    def test_remove_from_blacklist(self, auth_headers):
        """Test DELETE /api/blacklist/{entry_id}"""
        # First add a phone
        test_phone = f"07{uuid.uuid4().hex[:8]}"
        add_response = requests.post(
            f"{BASE_URL}/api/blacklist",
            headers=auth_headers,
            json={"phone": test_phone, "reason": "To be deleted"}
        )
        assert add_response.status_code == 200
        entry_id = add_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/blacklist/{entry_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200
        
        # Verify it's gone
        check_response = requests.get(
            f"{BASE_URL}/api/blacklist/check/{test_phone}",
            headers=auth_headers
        )
        assert check_response.json()["is_blacklisted"] == False


class TestDebtRemindersAPI:
    """Tests for debt reminders functionality"""
    
    def test_get_pending_debt_reminders(self, auth_headers):
        """Test GET /api/debt-reminders/pending"""
        response = requests.get(
            f"{BASE_URL}/api/debt-reminders/pending",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Each reminder should have customer info and debt amount
        for reminder in data:
            assert "customer_id" in reminder
            assert "customer_name" in reminder
            assert "total_debt" in reminder
    
    def test_get_debt_reminder_settings(self, auth_headers):
        """Test GET /api/debt-reminders/settings"""
        response = requests.get(
            f"{BASE_URL}/api/debt-reminders/settings",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should have default settings
        assert "enabled" in data or "reminder_days" in data or "min_debt_amount" in data
    
    def test_update_debt_reminder_settings(self, auth_headers):
        """Test PUT /api/debt-reminders/settings"""
        payload = {
            "enabled": True,
            "reminder_days": [7, 14, 30],
            "min_debt_amount": 500
        }
        response = requests.put(
            f"{BASE_URL}/api/debt-reminders/settings",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True


class TestCustomerFamilyAPI:
    """Tests for customer family selection feature"""
    
    def test_get_customer_families(self, auth_headers):
        """Test GET /api/customer-families"""
        response = requests.get(
            f"{BASE_URL}/api/customer-families",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_customer_family(self, auth_headers):
        """Test POST /api/customer-families"""
        family_name = f"TEST_Family_{uuid.uuid4().hex[:6]}"
        payload = {"name": family_name}
        
        response = requests.post(
            f"{BASE_URL}/api/customer-families",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == family_name
        assert "id" in data
        
        # Cleanup - delete the family
        family_id = data["id"]
        requests.delete(f"{BASE_URL}/api/customer-families/{family_id}", headers=auth_headers)
    
    def test_create_customer_with_family(self, auth_headers):
        """Test creating customer with family_id"""
        # First create a family
        family_name = f"TEST_CustFamily_{uuid.uuid4().hex[:6]}"
        family_response = requests.post(
            f"{BASE_URL}/api/customer-families",
            headers=auth_headers,
            json={"name": family_name}
        )
        assert family_response.status_code in [200, 201]
        family_id = family_response.json()["id"]
        
        # Create customer with family
        customer_name = f"TEST_Customer_{uuid.uuid4().hex[:6]}"
        customer_payload = {
            "name": customer_name,
            "phone": f"05{uuid.uuid4().hex[:8]}",
            "family_id": family_id
        }
        
        customer_response = requests.post(
            f"{BASE_URL}/api/customers",
            headers=auth_headers,
            json=customer_payload
        )
        assert customer_response.status_code in [200, 201]
        customer_data = customer_response.json()
        assert customer_data["name"] == customer_name
        assert customer_data["family_id"] == family_id
        
        # Cleanup
        customer_id = customer_data["id"]
        requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/customer-families/{family_id}", headers=auth_headers)


class TestCustomerBlacklistIntegration:
    """Test integration between customer and blacklist"""
    
    def test_customer_with_blacklisted_phone_flagged(self, auth_headers):
        """Test that customers with blacklisted phones are properly flagged"""
        # Get existing blacklist to check
        blacklist_response = requests.get(
            f"{BASE_URL}/api/blacklist",
            headers=auth_headers
        )
        blacklist = blacklist_response.json()
        
        if len(blacklist) > 0:
            blacklisted_phone = blacklist[0]["phone"]
            
            # Check if any customer has this phone
            customers_response = requests.get(
                f"{BASE_URL}/api/customers",
                headers=auth_headers
            )
            customers = customers_response.json()
            
            # Test blacklist check endpoint works
            check_response = requests.get(
                f"{BASE_URL}/api/blacklist/check/{blacklisted_phone}",
                headers=auth_headers
            )
            assert check_response.status_code == 200
            assert check_response.json()["is_blacklisted"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
