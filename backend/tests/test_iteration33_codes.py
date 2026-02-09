"""
Test iteration 33 features:
1. Code generation endpoints for purchases, daily sessions, and inventory
2. OCR button in Edit Product page
"""

import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCodeGenerationEndpoints:
    """Test all code generation endpoints with new formats"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for all tests"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_purchase_code_generation_format(self):
        """Test /api/purchases/generate-code returns AC0001/26 format"""
        response = requests.get(f"{BASE_URL}/api/purchases/generate-code", headers=self.headers)
        print(f"Purchase code response: {response.status_code} - {response.text}")
        
        assert response.status_code == 200, f"Failed to generate purchase code: {response.text}"
        data = response.json()
        
        assert "code" in data, "Response missing 'code' field"
        code = data["code"]
        
        # Should match format AC0001/26 (AC + 4 digits + / + 2 digit year)
        pattern = r'^AC\d{4}/\d{2}$'
        assert re.match(pattern, code), f"Purchase code '{code}' does not match expected format AC0001/26"
        
        # Verify year is 26 for 2026
        year_part = code.split('/')[1]
        assert year_part == "26", f"Year part should be '26', got '{year_part}'"
        
        print(f"✓ Purchase code format correct: {code}")
    
    def test_session_code_generation_format(self):
        """Test /api/daily-sessions/generate-code returns S001/26 format"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions/generate-code", headers=self.headers)
        print(f"Session code response: {response.status_code} - {response.text}")
        
        assert response.status_code == 200, f"Failed to generate session code: {response.text}"
        data = response.json()
        
        assert "code" in data, "Response missing 'code' field"
        code = data["code"]
        
        # Should match format S001/26 (S + 3 digits + / + 2 digit year)
        pattern = r'^S\d{3}/\d{2}$'
        assert re.match(pattern, code), f"Session code '{code}' does not match expected format S001/26"
        
        # Verify year is 26 for 2026
        year_part = code.split('/')[1]
        assert year_part == "26", f"Year part should be '26', got '{year_part}'"
        
        print(f"✓ Session code format correct: {code}")
    
    def test_inventory_code_generation_format(self):
        """Test /api/inventory-sessions/generate-code returns IN0001/26 format"""
        response = requests.get(f"{BASE_URL}/api/inventory-sessions/generate-code", headers=self.headers)
        print(f"Inventory code response: {response.status_code} - {response.text}")
        
        assert response.status_code == 200, f"Failed to generate inventory code: {response.text}"
        data = response.json()
        
        assert "code" in data, "Response missing 'code' field"
        code = data["code"]
        
        # Should match format IN0001/26 (IN + 4 digits + / + 2 digit year)
        pattern = r'^IN\d{4}/\d{2}$'
        assert re.match(pattern, code), f"Inventory code '{code}' does not match expected format IN0001/26"
        
        # Verify year is 26 for 2026
        year_part = code.split('/')[1]
        assert year_part == "26", f"Year part should be '26', got '{year_part}'"
        
        print(f"✓ Inventory code format correct: {code}")
    
    def test_expense_code_generation_format(self):
        """Test /api/expenses/generate-code returns CH0001/26 format"""
        response = requests.get(f"{BASE_URL}/api/expenses/generate-code", headers=self.headers)
        print(f"Expense code response: {response.status_code} - {response.text}")
        
        assert response.status_code == 200, f"Failed to generate expense code: {response.text}"
        data = response.json()
        
        assert "code" in data, "Response missing 'code' field"
        code = data["code"]
        
        # Should match format CH0001/26 (CH + 4 digits + / + 2 digit year)
        pattern = r'^CH\d{4}/\d{2}$'
        assert re.match(pattern, code), f"Expense code '{code}' does not match expected format CH0001/26"
        
        print(f"✓ Expense code format correct: {code}")
    
    def test_sale_code_generation_format(self):
        """Test /api/sales/generate-code returns BV0001/26 format"""
        response = requests.get(f"{BASE_URL}/api/sales/generate-code", headers=self.headers)
        print(f"Sale code response: {response.status_code} - {response.text}")
        
        assert response.status_code == 200, f"Failed to generate sale code: {response.text}"
        data = response.json()
        
        assert "code" in data, "Response missing 'code' field"
        code = data["code"]
        
        # Should match format BV0001/26 (BV + 4 digits + / + 2 digit year)
        pattern = r'^BV\d{4}/\d{2}$'
        assert re.match(pattern, code), f"Sale code '{code}' does not match expected format BV0001/26"
        
        print(f"✓ Sale code format correct: {code}")


class TestOCREndpoint:
    """Test OCR endpoint availability"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for all tests"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_ocr_endpoint_exists(self):
        """Test that OCR extract-models endpoint exists"""
        # We'll test with a small base64 test image (1x1 pixel white PNG)
        # This tests that the endpoint exists and responds
        test_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        response = requests.post(f"{BASE_URL}/api/ocr/extract-models", 
                                json={"image_base64": test_base64},
                                headers=self.headers)
        
        print(f"OCR response: {response.status_code} - {response.text}")
        
        # The endpoint should exist (200 or some error response related to image processing, not 404)
        assert response.status_code != 404, "OCR endpoint not found"
        
        # If 200, check structure
        if response.status_code == 200:
            data = response.json()
            assert "extracted_models" in data, "Response missing 'extracted_models' field"
            print(f"✓ OCR endpoint working, extracted_models: {data['extracted_models']}")
        else:
            print(f"⚠ OCR endpoint returned {response.status_code} - may need API key")


class TestDailySessionsAPI:
    """Test daily sessions API for code display"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for all tests"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_daily_sessions_endpoint(self):
        """Test /api/daily-sessions endpoint"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions", headers=self.headers)
        print(f"Daily sessions response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get daily sessions: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Daily sessions endpoint working, count: {len(data)}")
    
    def test_current_session_endpoint(self):
        """Test /api/daily-sessions/current endpoint"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions/current", headers=self.headers)
        print(f"Current session response: {response.status_code}")
        
        # Should be 200 (with session) or 404 (no current session)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"✓ Current session endpoint working")


class TestInventorySessionsAPI:
    """Test inventory sessions API for code display"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for all tests"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_inventory_sessions_endpoint(self):
        """Test /api/inventory-sessions endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory-sessions", headers=self.headers)
        print(f"Inventory sessions response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get inventory sessions: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Inventory sessions endpoint working, count: {len(data)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
