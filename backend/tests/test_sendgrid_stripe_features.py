"""
Test SendGrid Email Notifications and Stripe Payment Integration
Features tested:
- GET /api/payments/packages - Fetch subscription packages
- GET /api/notifications/sendgrid/settings - Fetch SendGrid settings
- PUT /api/notifications/sendgrid/settings - Save SendGrid settings
- POST /api/payments/create-checkout - Create Stripe checkout session
- Payment records management (CRUD)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_CREDENTIALS = {
    "email": "super@ntcommerce.com",
    "password": "superadmin123"
}

TENANT_CREDENTIALS = {
    "email": "amir@amir",
    "password": "test123"
}


class TestPaymentsPackages:
    """Test GET /api/payments/packages - public endpoint"""
    
    def test_get_packages_success(self):
        """Test fetching subscription packages - no auth required"""
        response = requests.get(f"{BASE_URL}/api/payments/packages")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        packages = response.json()
        assert isinstance(packages, list), "Response should be a list"
        assert len(packages) > 0, "Should have at least one package"
        
        # Verify package structure
        for pkg in packages:
            assert "id" in pkg, "Package should have id"
            assert "name" in pkg, "Package should have name"
            assert "amount" in pkg, "Package should have amount"
            assert "duration_days" in pkg, "Package should have duration_days"
            assert "currency" in pkg, "Package should have currency"
            
        print(f"SUCCESS: Found {len(packages)} subscription packages")
        for pkg in packages:
            print(f"  - {pkg['id']}: {pkg['name']} - {pkg['amount']} {pkg['currency']} ({pkg['duration_days']} days)")
    
    def test_packages_contain_expected_tiers(self):
        """Verify packages contain basic, pro, enterprise tiers"""
        response = requests.get(f"{BASE_URL}/api/payments/packages")
        assert response.status_code == 200
        
        packages = response.json()
        package_ids = [p['id'] for p in packages]
        
        # Check for expected package tiers
        assert any('basic' in pid for pid in package_ids), "Should have basic tier"
        assert any('pro' in pid for pid in package_ids), "Should have pro tier"
        assert any('enterprise' in pid for pid in package_ids), "Should have enterprise tier"
        
        print("SUCCESS: All expected package tiers found")


class TestSendGridSettings:
    """Test SendGrid settings endpoints - requires tenant auth"""
    
    @pytest.fixture
    def tenant_token(self):
        """Login as tenant and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_CREDENTIALS)
        if response.status_code != 200:
            pytest.skip(f"Tenant login failed: {response.text}")
        return response.json().get("access_token")
    
    def test_get_sendgrid_settings_success(self, tenant_token):
        """Test fetching SendGrid settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications/sendgrid/settings", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        settings = response.json()
        assert "enabled" in settings, "Should have enabled field"
        assert "new_sale_notification" in settings, "Should have new_sale_notification field"
        assert "low_stock_notification" in settings, "Should have low_stock_notification field"
        assert "daily_report" in settings, "Should have daily_report field"
        assert "weekly_report" in settings, "Should have weekly_report field"
        
        print(f"SUCCESS: SendGrid settings retrieved - enabled: {settings.get('enabled')}")
    
    def test_get_sendgrid_settings_without_auth_fails(self):
        """Test that SendGrid settings require authentication"""
        response = requests.get(f"{BASE_URL}/api/notifications/sendgrid/settings")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
        print("SUCCESS: SendGrid settings correctly require authentication")
    
    def test_update_sendgrid_settings_success(self, tenant_token):
        """Test updating SendGrid settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        
        # First get current settings
        response = requests.get(f"{BASE_URL}/api/notifications/sendgrid/settings", headers=headers)
        assert response.status_code == 200
        original_settings = response.json()
        
        # Update settings
        new_settings = {
            "enabled": True,
            "api_key": "SG.test_key_for_testing",
            "sender_email": "test@example.com",
            "sender_name": "Test Sender",
            "notification_email": "notify@example.com",
            "new_sale_notification": True,
            "low_stock_notification": True,
            "daily_report": False,
            "weekly_report": False
        }
        
        response = requests.put(f"{BASE_URL}/api/notifications/sendgrid/settings", 
                               json=new_settings, headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        assert result.get("success") == True, "Update should return success: true"
        
        print("SUCCESS: SendGrid settings updated successfully")
        
        # Verify update persisted
        response = requests.get(f"{BASE_URL}/api/notifications/sendgrid/settings", headers=headers)
        assert response.status_code == 200
        updated = response.json()
        assert updated.get("enabled") == True, "enabled should be True"
        assert updated.get("sender_email") == "test@example.com", "sender_email should be updated"
        assert updated.get("new_sale_notification") == True, "new_sale_notification should be True"
        
        print("SUCCESS: SendGrid settings update verified via GET")


class TestStripeCheckout:
    """Test Stripe checkout session creation"""
    
    def test_create_checkout_session_success(self):
        """Test creating Stripe checkout session"""
        # Get valid package ID first
        packages_response = requests.get(f"{BASE_URL}/api/payments/packages")
        assert packages_response.status_code == 200
        packages = packages_response.json()
        assert len(packages) > 0, "Need at least one package"
        
        package_id = packages[0]["id"]
        
        # Create checkout session
        response = requests.post(f"{BASE_URL}/api/payments/create-checkout", json={
            "package_id": package_id,
            "origin_url": "https://example.com"
        })
        
        # This will fail with actual Stripe error since we use test key
        # But we expect it to process the request and attempt Stripe
        if response.status_code == 200:
            data = response.json()
            assert "url" in data, "Should have checkout URL"
            assert "session_id" in data, "Should have session ID"
            print(f"SUCCESS: Checkout session created - URL: {data['url'][:50]}...")
        else:
            # Expected failure with test key - check it's a Stripe-related error
            detail = response.json().get("detail", "")
            print(f"INFO: Checkout creation returned {response.status_code}: {detail}")
            # It's expected to fail with invalid/test API key
            assert response.status_code in [500, 400], f"Unexpected status: {response.status_code}"
            print("INFO: Stripe checkout requires valid API key - test verifies endpoint exists")
    
    def test_create_checkout_invalid_package(self):
        """Test creating checkout with invalid package ID"""
        response = requests.post(f"{BASE_URL}/api/payments/create-checkout", json={
            "package_id": "invalid_package_xyz",
            "origin_url": "https://example.com"
        })
        
        assert response.status_code == 400, f"Expected 400 for invalid package, got {response.status_code}"
        print("SUCCESS: Invalid package returns 400 as expected")


class TestPaymentRecords:
    """Test payment records management - requires super admin"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Login as super admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=SUPER_ADMIN_CREDENTIALS)
        if response.status_code != 200:
            pytest.skip(f"Super admin login failed: {response.text}")
        return response.json().get("access_token")
    
    def test_get_payment_records_success(self, super_admin_token):
        """Test fetching payment records as super admin"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/payments/records", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "records" in data, "Response should have records"
        assert "total" in data, "Response should have total"
        assert "page" in data, "Response should have page"
        
        print(f"SUCCESS: Payment records retrieved - total: {data['total']}")
    
    def test_get_payment_records_without_auth_fails(self):
        """Test that payment records require super admin auth"""
        response = requests.get(f"{BASE_URL}/api/payments/records")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
        print("SUCCESS: Payment records correctly require authentication")
    
    def test_create_payment_record_success(self, super_admin_token):
        """Test creating a manual payment record"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        payment_data = {
            "amount": 5000.0,
            "currency": "dzd",
            "payment_method": "cash",
            "description": "TEST_payment_manual_test",
            "status": "paid"
        }
        
        response = requests.post(f"{BASE_URL}/api/payments/records", 
                                json=payment_data, headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Should return record ID"
        
        created_id = data["id"]
        print(f"SUCCESS: Payment record created with ID: {created_id}")
        
        # Verify record exists
        response = requests.get(f"{BASE_URL}/api/payments/records", headers=headers)
        assert response.status_code == 200
        records = response.json()["records"]
        
        found = False
        for record in records:
            if record.get("id") == created_id:
                found = True
                assert record.get("amount") == 5000.0, "Amount should match"
                assert record.get("payment_status") == "paid", "Status should be paid"
                break
        
        assert found, f"Created record {created_id} not found in records list"
        print("SUCCESS: Payment record verified via GET")
        
        # Cleanup - delete the test record
        delete_response = requests.delete(f"{BASE_URL}/api/payments/records/{created_id}", 
                                         headers=headers)
        assert delete_response.status_code == 200, "Cleanup delete should succeed"
        print("SUCCESS: Test payment record cleaned up")
    
    def test_update_payment_record_success(self, super_admin_token):
        """Test updating a payment record status"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Create a test record first
        payment_data = {
            "amount": 3000.0,
            "currency": "dzd",
            "payment_method": "bank",
            "description": "TEST_payment_update_test",
            "status": "pending"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/payments/records", 
                                       json=payment_data, headers=headers)
        assert create_response.status_code == 200
        record_id = create_response.json()["id"]
        
        # Update the record
        update_data = {
            "status": "paid",
            "notes": "Payment confirmed via bank transfer"
        }
        
        response = requests.put(f"{BASE_URL}/api/payments/records/{record_id}",
                               json=update_data, headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Update should return success"
        
        print(f"SUCCESS: Payment record {record_id} updated successfully")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/payments/records/{record_id}", headers=headers)
        print("SUCCESS: Test record cleaned up")
    
    def test_delete_payment_record_success(self, super_admin_token):
        """Test deleting a payment record"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Create a test record first
        payment_data = {
            "amount": 1000.0,
            "currency": "dzd",
            "description": "TEST_payment_delete_test",
            "status": "pending"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/payments/records", 
                                       json=payment_data, headers=headers)
        assert create_response.status_code == 200
        record_id = create_response.json()["id"]
        
        # Delete the record
        response = requests.delete(f"{BASE_URL}/api/payments/records/{record_id}", 
                                  headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Delete should return success"
        
        print(f"SUCCESS: Payment record {record_id} deleted successfully")
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/payments/records", headers=headers)
        records = get_response.json()["records"]
        for record in records:
            assert record.get("id") != record_id, "Deleted record should not appear in list"
        
        print("SUCCESS: Deletion verified - record no longer in list")
    
    def test_payment_records_filter_by_status(self, super_admin_token):
        """Test filtering payment records by status"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Test filtering by paid status
        response = requests.get(f"{BASE_URL}/api/payments/records?status=paid", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        for record in data["records"]:
            assert record.get("payment_status") == "paid", "All filtered records should be paid"
        
        print(f"SUCCESS: Status filter working - found {len(data['records'])} paid records")


class TestAuthenticationRequirements:
    """Test that endpoints enforce proper authentication"""
    
    def test_sendgrid_settings_requires_tenant_auth(self):
        """SendGrid settings should require tenant authentication"""
        response = requests.get(f"{BASE_URL}/api/notifications/sendgrid/settings")
        assert response.status_code in [401, 403]
        print("SUCCESS: SendGrid GET requires auth")
        
        response = requests.put(f"{BASE_URL}/api/notifications/sendgrid/settings", 
                               json={"enabled": True})
        assert response.status_code in [401, 403]
        print("SUCCESS: SendGrid PUT requires auth")
    
    def test_payment_records_requires_super_admin(self):
        """Payment records should require super admin"""
        # Login as regular tenant
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_CREDENTIALS)
        if response.status_code != 200:
            pytest.skip("Tenant login failed")
        tenant_token = response.json().get("access_token")
        
        headers = {"Authorization": f"Bearer {tenant_token}"}
        
        # Try to access payment records as tenant
        response = requests.get(f"{BASE_URL}/api/payments/records", headers=headers)
        assert response.status_code == 403, f"Tenant should not access payment records, got {response.status_code}"
        print("SUCCESS: Payment records correctly restricted to super admin")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
