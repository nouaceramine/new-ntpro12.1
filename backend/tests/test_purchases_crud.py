"""
Test suite for Purchases CRUD operations:
- GET /api/purchases/{id} - Get purchase details
- PUT /api/purchases/{id} - Update paid_amount and notes
- DELETE /api/purchases/{id} - Delete purchase

Author: Testing Agent
Date: 2026-01-xx
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable not set")

# Test credentials
TEST_USER_EMAIL = "test@test.com"
TEST_USER_PASSWORD = "test123"


class TestPurchasesCRUD:
    """Test suite for purchases CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.auth_token = None
        self.test_purchase_id = None
        self.test_supplier_id = None
        self.test_product_id = None
        
    def get_auth_token(self):
        """Authenticate and get token"""
        if self.auth_token:
            return self.auth_token
            
        response = self.session.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if response.status_code == 200:
            self.auth_token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            return self.auth_token
        else:
            pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
            
    def create_test_supplier(self):
        """Create a test supplier"""
        self.get_auth_token()
        
        supplier_data = {
            "name": f"TEST_Supplier_{uuid.uuid4().hex[:8]}",
            "phone": "0555123456",
            "email": "test_supplier@test.com",
            "address": "Test Address"
        }
        
        response = self.session.post(f"{BASE_URL}/api/suppliers", json=supplier_data)
        if response.status_code in [200, 201]:
            self.test_supplier_id = response.json().get("id")
            return self.test_supplier_id
        return None
        
    def create_test_product(self):
        """Create a test product"""
        self.get_auth_token()
        
        product_data = {
            "name_ar": f"TEST_منتج_{uuid.uuid4().hex[:8]}",
            "name_en": f"TEST_Product_{uuid.uuid4().hex[:8]}",
            "purchase_price": 100.00,
            "wholesale_price": 130.00,
            "retail_price": 150.00,
            "quantity": 10,
            "low_stock_threshold": 5
        }
        
        response = self.session.post(f"{BASE_URL}/api/products", json=product_data)
        if response.status_code in [200, 201]:
            self.test_product_id = response.json().get("id")
            return self.test_product_id
        return None
        
    def create_test_purchase(self):
        """Create a test purchase for testing"""
        self.get_auth_token()
        
        # Ensure we have a supplier and product
        if not self.test_supplier_id:
            self.create_test_supplier()
        if not self.test_product_id:
            self.create_test_product()
            
        if not self.test_supplier_id or not self.test_product_id:
            pytest.skip("Could not create test supplier or product")
            
        purchase_data = {
            "supplier_id": self.test_supplier_id,
            "items": [{
                "product_id": self.test_product_id,
                "product_name": "Test Product",
                "quantity": 5,
                "unit_price": 100.00,
                "total": 500.00
            }],
            "total": 500.00,
            "paid_amount": 200.00,
            "payment_method": "cash",
            "payment_type": "partial",
            "notes": "TEST_Initial purchase notes"
        }
        
        response = self.session.post(f"{BASE_URL}/api/purchases", json=purchase_data)
        if response.status_code in [200, 201]:
            self.test_purchase_id = response.json().get("id")
            return self.test_purchase_id
        return None
        
    def cleanup_test_data(self):
        """Cleanup test data created during tests"""
        self.get_auth_token()
        
        if self.test_purchase_id:
            self.session.delete(f"{BASE_URL}/api/purchases/{self.test_purchase_id}")
        if self.test_supplier_id:
            self.session.delete(f"{BASE_URL}/api/suppliers/{self.test_supplier_id}")
        if self.test_product_id:
            self.session.delete(f"{BASE_URL}/api/products/{self.test_product_id}")
    
    # ===========================================
    # GET /api/purchases/{id} Tests
    # ===========================================
    
    def test_get_purchase_by_id_success(self):
        """Test GET /api/purchases/{id} - should return purchase details"""
        self.get_auth_token()
        purchase_id = self.create_test_purchase()
        
        if not purchase_id:
            pytest.skip("Could not create test purchase")
            
        try:
            response = self.session.get(f"{BASE_URL}/api/purchases/{purchase_id}")
            
            # Assert status code
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            # Assert response structure
            data = response.json()
            assert "id" in data, "Response should contain 'id'"
            assert data["id"] == purchase_id, "Returned purchase ID should match requested ID"
            assert "total" in data, "Response should contain 'total'"
            assert "paid_amount" in data, "Response should contain 'paid_amount'"
            assert "remaining" in data, "Response should contain 'remaining'"
            assert "status" in data, "Response should contain 'status'"
            assert "items" in data, "Response should contain 'items'"
            
            # Assert data values
            assert data["total"] == 500.00, f"Expected total 500.00, got {data['total']}"
            assert data["paid_amount"] == 200.00, f"Expected paid_amount 200.00, got {data['paid_amount']}"
            assert data["remaining"] == 300.00, f"Expected remaining 300.00, got {data['remaining']}"
            assert data["status"] == "partial", f"Expected status 'partial', got {data['status']}"
            
            print(f"✓ GET /api/purchases/{purchase_id} - Success")
        finally:
            self.cleanup_test_data()
    
    def test_get_purchase_not_found(self):
        """Test GET /api/purchases/{id} - should return 404 for non-existent purchase"""
        self.get_auth_token()
        
        fake_id = f"non-existent-{uuid.uuid4()}"
        response = self.session.get(f"{BASE_URL}/api/purchases/{fake_id}")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ GET /api/purchases/{id} with non-existent ID - Returns 404")
    
    # ===========================================
    # PUT /api/purchases/{id} Tests
    # ===========================================
    
    def test_update_purchase_paid_amount(self):
        """Test PUT /api/purchases/{id} - update paid_amount"""
        self.get_auth_token()
        purchase_id = self.create_test_purchase()
        
        if not purchase_id:
            pytest.skip("Could not create test purchase")
            
        try:
            # Update paid amount from 200 to 400
            update_data = {
                "paid_amount": 400.00
            }
            
            response = self.session.put(f"{BASE_URL}/api/purchases/{purchase_id}", json=update_data)
            
            # Assert status code
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            # Assert response message
            data = response.json()
            assert "message" in data, "Response should contain message"
            assert "purchase" in data, "Response should contain updated purchase"
            
            # Verify the update via GET
            get_response = self.session.get(f"{BASE_URL}/api/purchases/{purchase_id}")
            assert get_response.status_code == 200
            
            updated_purchase = get_response.json()
            assert updated_purchase["paid_amount"] == 400.00, f"Expected paid_amount 400.00, got {updated_purchase['paid_amount']}"
            assert updated_purchase["remaining"] == 100.00, f"Expected remaining 100.00, got {updated_purchase['remaining']}"
            assert updated_purchase["status"] == "partial", f"Expected status 'partial', got {updated_purchase['status']}"
            
            print(f"✓ PUT /api/purchases/{purchase_id} - paid_amount updated successfully")
        finally:
            self.cleanup_test_data()
    
    def test_update_purchase_to_fully_paid(self):
        """Test PUT /api/purchases/{id} - update paid_amount to full amount (status becomes 'paid')"""
        self.get_auth_token()
        purchase_id = self.create_test_purchase()
        
        if not purchase_id:
            pytest.skip("Could not create test purchase")
            
        try:
            # Update paid amount to full amount
            update_data = {
                "paid_amount": 500.00
            }
            
            response = self.session.put(f"{BASE_URL}/api/purchases/{purchase_id}", json=update_data)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            # Verify via GET
            get_response = self.session.get(f"{BASE_URL}/api/purchases/{purchase_id}")
            updated_purchase = get_response.json()
            
            assert updated_purchase["paid_amount"] == 500.00
            assert updated_purchase["remaining"] == 0
            assert updated_purchase["status"] == "paid", f"Expected status 'paid', got {updated_purchase['status']}"
            
            print(f"✓ PUT /api/purchases/{purchase_id} - status changed to 'paid' when fully paid")
        finally:
            self.cleanup_test_data()
    
    def test_update_purchase_notes(self):
        """Test PUT /api/purchases/{id} - update notes"""
        self.get_auth_token()
        purchase_id = self.create_test_purchase()
        
        if not purchase_id:
            pytest.skip("Could not create test purchase")
            
        try:
            new_notes = "TEST_Updated notes - تم تحديث الملاحظات"
            update_data = {
                "notes": new_notes
            }
            
            response = self.session.put(f"{BASE_URL}/api/purchases/{purchase_id}", json=update_data)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            # Verify via GET
            get_response = self.session.get(f"{BASE_URL}/api/purchases/{purchase_id}")
            updated_purchase = get_response.json()
            
            assert updated_purchase["notes"] == new_notes, f"Notes not updated correctly"
            
            print(f"✓ PUT /api/purchases/{purchase_id} - notes updated successfully")
        finally:
            self.cleanup_test_data()
    
    def test_update_purchase_not_found(self):
        """Test PUT /api/purchases/{id} - should return 404 for non-existent purchase"""
        self.get_auth_token()
        
        fake_id = f"non-existent-{uuid.uuid4()}"
        update_data = {"paid_amount": 100.00}
        
        response = self.session.put(f"{BASE_URL}/api/purchases/{fake_id}", json=update_data)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ PUT /api/purchases/{id} with non-existent ID - Returns 404")
    
    # ===========================================
    # DELETE /api/purchases/{id} Tests
    # ===========================================
    
    def test_delete_purchase_success(self):
        """Test DELETE /api/purchases/{id} - should delete purchase and return success"""
        self.get_auth_token()
        purchase_id = self.create_test_purchase()
        
        if not purchase_id:
            pytest.skip("Could not create test purchase")
            
        # Don't cleanup since we're testing delete
        try:
            response = self.session.delete(f"{BASE_URL}/api/purchases/{purchase_id}")
            
            # Assert status code
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            # Assert response message
            data = response.json()
            assert "message" in data, "Response should contain message"
            assert "deleted_id" in data, "Response should contain deleted_id"
            assert data["deleted_id"] == purchase_id
            
            # Verify deletion - GET should return 404
            verify_response = self.session.get(f"{BASE_URL}/api/purchases/{purchase_id}")
            assert verify_response.status_code == 404, "Deleted purchase should return 404 on GET"
            
            print(f"✓ DELETE /api/purchases/{purchase_id} - Deleted successfully")
            
            # Mark as already deleted so cleanup doesn't try to delete again
            self.test_purchase_id = None
        finally:
            # Cleanup remaining test data (supplier, product)
            if self.test_supplier_id:
                self.session.delete(f"{BASE_URL}/api/suppliers/{self.test_supplier_id}")
            if self.test_product_id:
                self.session.delete(f"{BASE_URL}/api/products/{self.test_product_id}")
    
    def test_delete_purchase_not_found(self):
        """Test DELETE /api/purchases/{id} - should return 404 for non-existent purchase"""
        self.get_auth_token()
        
        fake_id = f"non-existent-{uuid.uuid4()}"
        response = self.session.delete(f"{BASE_URL}/api/purchases/{fake_id}")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ DELETE /api/purchases/{id} with non-existent ID - Returns 404")
    
    # ===========================================
    # Authentication Tests
    # ===========================================
    
    def test_endpoints_require_authentication(self):
        """Test that all purchase endpoints require authentication"""
        # Create a new session without auth
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        fake_id = str(uuid.uuid4())
        
        # Test GET without auth
        get_response = no_auth_session.get(f"{BASE_URL}/api/purchases/{fake_id}")
        assert get_response.status_code in [401, 403], f"GET should require auth, got {get_response.status_code}"
        
        # Test PUT without auth
        put_response = no_auth_session.put(f"{BASE_URL}/api/purchases/{fake_id}", json={"paid_amount": 100})
        assert put_response.status_code in [401, 403], f"PUT should require auth, got {put_response.status_code}"
        
        # Test DELETE without auth
        delete_response = no_auth_session.delete(f"{BASE_URL}/api/purchases/{fake_id}")
        assert delete_response.status_code in [401, 403], f"DELETE should require auth, got {delete_response.status_code}"
        
        print("✓ All purchase endpoints require authentication")


class TestGetPurchasesList:
    """Test suite for GET /api/purchases (list all)"""
    
    def test_get_purchases_list(self):
        """Test GET /api/purchases - should return list of purchases"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Authenticate
        auth_response = session.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if auth_response.status_code != 200:
            pytest.skip("Authentication failed")
            
        token = auth_response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get purchases list
        response = session.get(f"{BASE_URL}/api/purchases")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"✓ GET /api/purchases - Returns list with {len(data)} purchases")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
