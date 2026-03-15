"""
POS Page Redesign Tests
Tests for the redesigned Point of Sale functionality
Note: Some APIs require tenant context, super admin may get 403
"""
import requests
import pytest
from datetime import datetime

# Test configuration
BASE_URL = "https://nt-commerce-v12.preview.emergentagent.com/api"
SUPER_ADMIN = {"email": "test@test.com", "password": "test123"}


class TestPOSPublicAPIs:
    """Test public/semi-public POS-related API endpoints"""
    
    def test_login_works(self):
        """Test user login returns valid token"""
        response = requests.post(
            f"{BASE_URL}/auth/unified-login",
            json=SUPER_ADMIN
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 50
        print(f"Login successful, user_type: {data.get('user_type')}")
    
    def test_generate_sale_code(self):
        """Test sale code generation (public endpoint)"""
        response = requests.get(f"{BASE_URL}/sales/generate-code")
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert data["code"].startswith("BV")
        print(f"Generated sale code: {data['code']}")
    
    def test_get_wilayas(self):
        """Test delivery wilayas list (public endpoint)"""
        response = requests.get(f"{BASE_URL}/delivery/wilayas")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Got {len(data)} wilayas")
    
    def test_get_public_plans(self):
        """Test public plans endpoint"""
        response = requests.get(f"{BASE_URL}/saas/plans/public")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Got {len(data)} public plans")


class TestPOSAuthenticatedAPIs:
    """Test authenticated APIs that work with super admin"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication token for API calls"""
        response = requests.post(
            f"{BASE_URL}/auth/unified-login",
            json=SUPER_ADMIN
        )
        if response.status_code == 200:
            data = response.json()
            return {"Authorization": f"Bearer {data.get('access_token')}"}
        return {}
    
    def test_auth_me(self, auth_headers):
        """Test auth/me endpoint returns user info"""
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        print(f"User email: {data.get('email')}")


class TestPOSFrontendIntegration:
    """Test that frontend integration works"""
    
    def test_pos_page_loads(self):
        """Test POS page loads (via HTML response check)"""
        # This is a basic connectivity test
        response = requests.get(
            "https://nt-commerce-v12.preview.emergentagent.com/pos",
            allow_redirects=True
        )
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        print("POS page loads successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
