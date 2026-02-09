"""
Test POS Sales Flow - Testing the sale process and French translations for cash boxes
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "super@ntcommerce.com"
        return data["access_token"]


class TestCashBoxesFrenchTranslation:
    """Test French translation for cash boxes"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_cash_boxes(self, auth_token):
        """Test that cash boxes return French translation (name_fr)"""
        response = requests.get(f"{BASE_URL}/api/cash-boxes", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed to get cash boxes: {response.text}"
        
        cash_boxes = response.json()
        assert len(cash_boxes) > 0, "No cash boxes found"
        
        # Check that name_fr field exists for all boxes
        expected_fr_names = {
            "cash": "Caisse",
            "bank": "Compte bancaire",
            "wallet": "Portefeuille électronique",
            "safe": "Coffre-fort"
        }
        
        for box in cash_boxes:
            assert "name_fr" in box, f"Missing name_fr for box: {box.get('name')}"
            box_type = box.get("type")
            if box_type in expected_fr_names:
                assert box.get("name_fr") == expected_fr_names[box_type], \
                    f"Incorrect French name for {box_type}: expected {expected_fr_names[box_type]}, got {box.get('name_fr')}"
        
        print(f"✓ All {len(cash_boxes)} cash boxes have French translations")


class TestDailySessions:
    """Test daily sessions functionality"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_current_session(self, auth_token):
        """Test getting current daily session"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions/current", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        # Can be 200 (session exists) or 404 (no session)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            print(f"✓ Current session status: {data.get('status')}")
        else:
            print("✓ No current session (expected if none open)")
    
    def test_get_daily_sessions_list(self, auth_token):
        """Test getting list of daily sessions"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed to get sessions: {response.text}"
        
        sessions = response.json()
        assert isinstance(sessions, list), "Sessions should be a list"
        print(f"✓ Found {len(sessions)} daily sessions")


class TestSalesAPI:
    """Test sales API functionality"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_sales(self, auth_token):
        """Test getting sales list"""
        response = requests.get(f"{BASE_URL}/api/sales", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed to get sales: {response.text}"
        
        sales = response.json()
        assert isinstance(sales, list), "Sales should be a list"
        print(f"✓ Found {len(sales)} sales")
        
        if len(sales) > 0:
            # Verify sale structure
            sale = sales[0]
            required_fields = ["id", "invoice_number", "items", "total"]
            for field in required_fields:
                assert field in sale, f"Missing field {field} in sale"
            print(f"✓ Sale structure verified: {sale.get('invoice_number')}")
    
    def test_get_products(self, auth_token):
        """Test getting products list"""
        response = requests.get(f"{BASE_URL}/api/products", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed to get products: {response.text}"
        
        products = response.json()
        assert isinstance(products, list), "Products should be a list"
        print(f"✓ Found {len(products)} products")


class TestDashboardStats:
    """Test dashboard statistics"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_stats(self, auth_token):
        """Test getting dashboard statistics"""
        response = requests.get(f"{BASE_URL}/api/stats", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed to get stats: {response.text}"
        
        stats = response.json()
        
        # Check for cash_boxes with French names
        if "cash_boxes" in stats:
            for box in stats["cash_boxes"]:
                if "name_fr" in box:
                    print(f"  - Cash box {box.get('name')} -> {box.get('name_fr')}")
        
        print(f"✓ Dashboard stats retrieved successfully")
    
    def test_get_sales_stats(self, auth_token):
        """Test getting sales statistics for dashboard"""
        response = requests.get(f"{BASE_URL}/api/dashboard/sales-stats", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Failed to get sales stats: {response.text}"
        
        data = response.json()
        
        # Check for today, month, year stats
        expected_keys = ["today", "month", "year"]
        for key in expected_keys:
            assert key in data, f"Missing {key} in sales stats"
            assert "total" in data[key], f"Missing total in {key}"
            assert "count" in data[key], f"Missing count in {key}"
        
        print(f"✓ Sales stats: Today={data['today']['total']}, Month={data['month']['total']}, Year={data['year']['total']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
