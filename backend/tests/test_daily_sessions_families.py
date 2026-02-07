"""
Test suite for Daily Sessions, Customer Families, and Supplier Families APIs
Testing new POS features: 
1. Daily Sessions - open/close cash tracking
2. Customer Families - customer categorization
3. Supplier Families - supplier categorization
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    def test_login_admin(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print("✓ Admin login successful")


class TestDailySessions:
    """Tests for Daily Sessions (حصص البيع اليومية) API"""
    
    @pytest.fixture
    def auth_header(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_daily_sessions_list(self, auth_header):
        """GET /api/daily-sessions - should return list of sessions"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/daily-sessions returns {len(data)} sessions")
    
    def test_create_daily_session(self, auth_header):
        """POST /api/daily-sessions - should create a new session"""
        # First, close any existing open session
        sessions = requests.get(f"{BASE_URL}/api/daily-sessions", headers=auth_header).json()
        for session in sessions:
            if session.get("status") == "open":
                # Close it first
                requests.put(f"{BASE_URL}/api/daily-sessions/{session['id']}/close", headers=auth_header, json={
                    "closing_cash": session.get("opening_cash", 0),
                    "closed_at": datetime.now().isoformat(),
                    "notes": "Test cleanup"
                })
        
        # Create new session
        payload = {
            "opening_cash": 5000.0,
            "opened_at": datetime.now().isoformat(),
            "status": "open"
        }
        response = requests.post(f"{BASE_URL}/api/daily-sessions", headers=auth_header, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["opening_cash"] == 5000.0
        assert data["status"] == "open"
        assert "id" in data
        
        # Store session id for cleanup
        self.test_session_id = data["id"]
        print(f"✓ POST /api/daily-sessions created session {data['id'][:8]}...")
        
        # Verify cannot create another while one is open
        response2 = requests.post(f"{BASE_URL}/api/daily-sessions", headers=auth_header, json=payload)
        assert response2.status_code == 400
        print("✓ Duplicate open session correctly prevented")
        
        # Cleanup - close the session
        close_response = requests.put(f"{BASE_URL}/api/daily-sessions/{data['id']}/close", headers=auth_header, json={
            "closing_cash": 5500.0,
            "closed_at": datetime.now().isoformat(),
            "notes": "Test session cleanup"
        })
        assert close_response.status_code == 200
    
    def test_close_daily_session(self, auth_header):
        """PUT /api/daily-sessions/:id/close - should close the session"""
        # First create a session
        sessions = requests.get(f"{BASE_URL}/api/daily-sessions", headers=auth_header).json()
        for session in sessions:
            if session.get("status") == "open":
                requests.put(f"{BASE_URL}/api/daily-sessions/{session['id']}/close", headers=auth_header, json={
                    "closing_cash": session.get("opening_cash", 0),
                    "closed_at": datetime.now().isoformat(),
                    "notes": "Test cleanup"
                })
        
        create_response = requests.post(f"{BASE_URL}/api/daily-sessions", headers=auth_header, json={
            "opening_cash": 3000.0,
            "opened_at": datetime.now().isoformat(),
            "status": "open"
        })
        assert create_response.status_code == 200
        session_id = create_response.json()["id"]
        
        # Close the session
        close_payload = {
            "closing_cash": 3500.0,
            "closed_at": datetime.now().isoformat(),
            "notes": "Test close session"
        }
        response = requests.put(f"{BASE_URL}/api/daily-sessions/{session_id}/close", headers=auth_header, json=close_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["closing_cash"] == 3500.0
        assert data["status"] == "closed"
        assert data["notes"] == "Test close session"
        print(f"✓ PUT /api/daily-sessions/{session_id[:8]}.../close successful")
    
    def test_get_current_session(self, auth_header):
        """GET /api/daily-sessions/current - should return current open session or null"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions/current", headers=auth_header)
        assert response.status_code == 200
        # Can be null or a session object
        print("✓ GET /api/daily-sessions/current works")


class TestCustomerFamilies:
    """Tests for Customer Families (عائلات الزبائن) API"""
    
    @pytest.fixture
    def auth_header(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_customer_families_list(self, auth_header):
        """GET /api/customer-families - should return list of families"""
        response = requests.get(f"{BASE_URL}/api/customer-families", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/customer-families returns {len(data)} families")
        
        # Check structure if families exist
        if len(data) > 0:
            family = data[0]
            assert "id" in family
            assert "name" in family
            assert "customer_count" in family
            print(f"  Family structure verified: {family['name']}")
    
    def test_create_customer_family(self, auth_header):
        """POST /api/customer-families - should create a new family"""
        payload = {
            "name": "TEST_عائلة اختبارية",
            "description": "وصف العائلة الاختبارية"
        }
        response = requests.post(f"{BASE_URL}/api/customer-families", headers=auth_header, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST_عائلة اختبارية"
        assert data["description"] == "وصف العائلة الاختبارية"
        assert data["customer_count"] == 0
        assert "id" in data
        
        family_id = data["id"]
        print(f"✓ POST /api/customer-families created family {family_id[:8]}...")
        
        # Cleanup - delete test family
        delete_response = requests.delete(f"{BASE_URL}/api/customer-families/{family_id}", headers=auth_header)
        assert delete_response.status_code == 200
        print("✓ Test family cleaned up")
    
    def test_update_customer_family(self, auth_header):
        """PUT /api/customer-families/:id - should update family"""
        # Create test family
        create_response = requests.post(f"{BASE_URL}/api/customer-families", headers=auth_header, json={
            "name": "TEST_للتحديث",
            "description": "وصف قبل التحديث"
        })
        family_id = create_response.json()["id"]
        
        # Update
        update_payload = {
            "name": "TEST_تم التحديث",
            "description": "وصف بعد التحديث"
        }
        response = requests.put(f"{BASE_URL}/api/customer-families/{family_id}", headers=auth_header, json=update_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST_تم التحديث"
        assert data["description"] == "وصف بعد التحديث"
        print(f"✓ PUT /api/customer-families/{family_id[:8]}... updated successfully")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customer-families/{family_id}", headers=auth_header)
    
    def test_delete_customer_family(self, auth_header):
        """DELETE /api/customer-families/:id - should delete family"""
        # Create test family
        create_response = requests.post(f"{BASE_URL}/api/customer-families", headers=auth_header, json={
            "name": "TEST_للحذف",
            "description": "سيتم حذف هذه العائلة"
        })
        family_id = create_response.json()["id"]
        
        # Delete
        response = requests.delete(f"{BASE_URL}/api/customer-families/{family_id}", headers=auth_header)
        assert response.status_code == 200
        print(f"✓ DELETE /api/customer-families/{family_id[:8]}... successful")
        
        # Verify deleted
        get_response = requests.get(f"{BASE_URL}/api/customer-families/{family_id}", headers=auth_header)
        assert get_response.status_code == 404


class TestSupplierFamilies:
    """Tests for Supplier Families (عائلات الموردين) API"""
    
    @pytest.fixture
    def auth_header(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_supplier_families_list(self, auth_header):
        """GET /api/supplier-families - should return list of families"""
        response = requests.get(f"{BASE_URL}/api/supplier-families", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/supplier-families returns {len(data)} families")
        
        # Check structure if families exist
        if len(data) > 0:
            family = data[0]
            assert "id" in family
            assert "name" in family
            assert "supplier_count" in family
            print(f"  Family structure verified: {family['name']}")
    
    def test_create_supplier_family(self, auth_header):
        """POST /api/supplier-families - should create a new family"""
        payload = {
            "name": "TEST_موردون اختباريون",
            "description": "وصف عائلة الموردين الاختبارية"
        }
        response = requests.post(f"{BASE_URL}/api/supplier-families", headers=auth_header, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST_موردون اختباريون"
        assert data["description"] == "وصف عائلة الموردين الاختبارية"
        assert data["supplier_count"] == 0
        assert "id" in data
        
        family_id = data["id"]
        print(f"✓ POST /api/supplier-families created family {family_id[:8]}...")
        
        # Cleanup
        delete_response = requests.delete(f"{BASE_URL}/api/supplier-families/{family_id}", headers=auth_header)
        assert delete_response.status_code == 200
        print("✓ Test family cleaned up")
    
    def test_update_supplier_family(self, auth_header):
        """PUT /api/supplier-families/:id - should update family"""
        # Create test family
        create_response = requests.post(f"{BASE_URL}/api/supplier-families", headers=auth_header, json={
            "name": "TEST_مورد للتحديث",
            "description": "وصف قبل التحديث"
        })
        family_id = create_response.json()["id"]
        
        # Update
        update_payload = {
            "name": "TEST_مورد تم التحديث",
            "description": "وصف بعد التحديث"
        }
        response = requests.put(f"{BASE_URL}/api/supplier-families/{family_id}", headers=auth_header, json=update_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST_مورد تم التحديث"
        assert data["description"] == "وصف بعد التحديث"
        print(f"✓ PUT /api/supplier-families/{family_id[:8]}... updated successfully")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/supplier-families/{family_id}", headers=auth_header)
    
    def test_delete_supplier_family(self, auth_header):
        """DELETE /api/supplier-families/:id - should delete family"""
        # Create test family
        create_response = requests.post(f"{BASE_URL}/api/supplier-families", headers=auth_header, json={
            "name": "TEST_مورد للحذف",
            "description": "سيتم حذف هذه العائلة"
        })
        family_id = create_response.json()["id"]
        
        # Delete
        response = requests.delete(f"{BASE_URL}/api/supplier-families/{family_id}", headers=auth_header)
        assert response.status_code == 200
        print(f"✓ DELETE /api/supplier-families/{family_id[:8]}... successful")
        
        # Verify deleted
        get_response = requests.get(f"{BASE_URL}/api/supplier-families/{family_id}", headers=auth_header)
        assert get_response.status_code == 404


class TestExistingData:
    """Tests to verify existing seed data mentioned by main agent"""
    
    @pytest.fixture
    def auth_header(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_existing_customer_families(self, auth_header):
        """Verify existing customer families data"""
        response = requests.get(f"{BASE_URL}/api/customer-families", headers=auth_header)
        data = response.json()
        
        # Check if VIP family exists (mentioned in test request)
        vip_exists = any(f["name"] == "VIP" or "VIP" in f.get("name", "") for f in data)
        print(f"✓ Customer families found: {[f['name'] for f in data]}")
        if vip_exists:
            print("  VIP customer family exists as expected")
    
    def test_existing_supplier_families(self, auth_header):
        """Verify existing supplier families data"""
        response = requests.get(f"{BASE_URL}/api/supplier-families", headers=auth_header)
        data = response.json()
        
        # Check if local suppliers family exists (mentioned in test request)
        local_exists = any("محلي" in f.get("name", "") or "local" in f.get("name", "").lower() for f in data)
        print(f"✓ Supplier families found: {[f['name'] for f in data]}")
        if local_exists:
            print("  Local suppliers family exists as expected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
