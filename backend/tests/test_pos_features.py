"""
Tests for new POS features:
1. Receipt settings API (GET/POST)
2. Sales API with date filters
3. Product history (purchase/sales/price)
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"

# Test credentials
TEST_EMAIL = "admin@test.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token") or response.json().get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestReceiptSettingsAPI:
    """Receipt Settings API tests - GET /api/settings/receipt and POST /api/settings/receipt"""

    def test_get_receipt_settings_default(self, api_client):
        """GET /api/settings/receipt - should return default settings if not configured"""
        response = api_client.get(f"{BASE_URL}/api/settings/receipt")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Validate default structure
        assert "auto_print" in data, "Missing auto_print field"
        assert "show_print_dialog" in data, "Missing show_print_dialog field"
        assert "default_template_id" in data, "Missing default_template_id field"
        assert "templates" in data, "Missing templates field"
        
        # Validate templates structure
        templates = data.get("templates", [])
        assert len(templates) >= 1, "Should have at least one template"
        
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "width" in template

    def test_update_receipt_settings(self, api_client):
        """POST /api/settings/receipt - should update and save settings"""
        new_settings = {
            "auto_print": True,
            "show_print_dialog": False,
            "default_template_id": "default_58mm",
            "templates": [
                {
                    "id": "default_58mm",
                    "name": "Thermal 58mm",
                    "name_ar": "حراري 58 مم",
                    "width": "58mm",
                    "show_logo": False,
                    "show_header": True,
                    "show_footer": True,
                    "header_text": "Test Header",
                    "footer_text": "شكراً لزيارتكم",
                    "font_size": "small",
                    "is_default": True
                },
                {
                    "id": "default_80mm",
                    "name": "Thermal 80mm",
                    "name_ar": "حراري 80 مم",
                    "width": "80mm",
                    "show_logo": True,
                    "show_header": True,
                    "show_footer": True,
                    "header_text": "",
                    "footer_text": "شكراً لزيارتكم",
                    "font_size": "normal",
                    "is_default": False
                }
            ]
        }
        
        response = api_client.post(f"{BASE_URL}/api/settings/receipt", json=new_settings)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify the settings were persisted
        get_response = api_client.get(f"{BASE_URL}/api/settings/receipt")
        assert get_response.status_code == 200
        saved_data = get_response.json()
        
        assert saved_data.get("auto_print") == True, "auto_print should be updated to True"
        assert saved_data.get("default_template_id") == "default_58mm", "default_template_id should be updated"

    def test_reset_receipt_settings(self, api_client):
        """POST /api/settings/receipt - reset back to default values"""
        default_settings = {
            "auto_print": False,
            "show_print_dialog": True,
            "default_template_id": "default_80mm",
            "templates": [
                {
                    "id": "default_58mm",
                    "name": "Thermal 58mm",
                    "name_ar": "حراري 58 مم",
                    "width": "58mm",
                    "show_logo": False,
                    "show_header": True,
                    "show_footer": True
                },
                {
                    "id": "default_80mm",
                    "name": "Thermal 80mm",
                    "name_ar": "حراري 80 مم",
                    "width": "80mm",
                    "show_logo": True,
                    "show_header": True,
                    "show_footer": True
                },
                {
                    "id": "default_a4",
                    "name": "A4 Full Page",
                    "name_ar": "صفحة A4 كاملة",
                    "width": "A4",
                    "show_logo": True,
                    "show_header": True,
                    "show_footer": True
                }
            ]
        }
        
        response = api_client.post(f"{BASE_URL}/api/settings/receipt", json=default_settings)
        assert response.status_code == 200


class TestSalesAPIWithFilters:
    """Sales API tests - GET /api/sales with date filters"""

    def test_get_all_sales(self, api_client):
        """GET /api/sales - should return list of sales"""
        response = api_client.get(f"{BASE_URL}/api/sales")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # If we have sales, verify structure
        if len(data) > 0:
            sale = data[0]
            # Check key fields exist
            assert "id" in sale, "Sale should have id"
            assert "items" in sale or "total" in sale, "Sale should have items or total"

    def test_get_sales_today(self, api_client):
        """GET /api/sales with today filter"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = api_client.get(f"{BASE_URL}/api/sales?start_date={today}&end_date={today}T23:59:59")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_get_sales_week(self, api_client):
        """GET /api/sales with week filter"""
        today = datetime.now()
        week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        
        response = api_client.get(f"{BASE_URL}/api/sales?start_date={week_ago}&end_date={today_str}T23:59:59")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_get_sales_month(self, api_client):
        """GET /api/sales with month filter"""
        today = datetime.now()
        month_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        
        response = api_client.get(f"{BASE_URL}/api/sales?start_date={month_ago}&end_date={today_str}T23:59:59")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_get_sales_custom_range(self, api_client):
        """GET /api/sales with custom date range"""
        start = "2024-01-01"
        end = "2024-12-31T23:59:59"
        
        response = api_client.get(f"{BASE_URL}/api/sales?start_date={start}&end_date={end}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"


class TestProductHistoryAPI:
    """Product History API tests - purchase/sales/price history"""

    @pytest.fixture
    def sample_product_id(self, api_client):
        """Get a product ID from the database"""
        response = api_client.get(f"{BASE_URL}/api/products")
        if response.status_code == 200:
            products = response.json()
            if len(products) > 0:
                return products[0].get("id")
        return None

    def test_get_product_purchase_history(self, api_client, sample_product_id):
        """GET /api/products/{id}/purchase-history - should return purchase records"""
        if not sample_product_id:
            pytest.skip("No products in database")
        
        response = api_client.get(f"{BASE_URL}/api/products/{sample_product_id}/purchase-history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # If we have purchase history, verify structure
        if len(data) > 0:
            record = data[0]
            # Expected fields: date, supplier_name, quantity, unit_price, total
            print(f"Purchase history record keys: {record.keys()}")

    def test_get_product_sales_history(self, api_client, sample_product_id):
        """GET /api/products/{id}/sales-history - should return sales records"""
        if not sample_product_id:
            pytest.skip("No products in database")
        
        response = api_client.get(f"{BASE_URL}/api/products/{sample_product_id}/sales-history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_get_product_price_history(self, api_client, sample_product_id):
        """GET /api/price-history with product filter - should return price changes"""
        if not sample_product_id:
            pytest.skip("No products in database")
        
        response = api_client.get(f"{BASE_URL}/api/price-history?product_id={sample_product_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"


class TestSaleDetailAPI:
    """Sale Detail and Invoice APIs"""

    @pytest.fixture
    def sample_sale_id(self, api_client):
        """Get a sale ID from the database"""
        response = api_client.get(f"{BASE_URL}/api/sales")
        if response.status_code == 200:
            sales = response.json()
            if len(sales) > 0:
                return sales[0].get("id")
        return None

    def test_get_sale_detail(self, api_client, sample_sale_id):
        """GET /api/sales/{id} - should return sale details"""
        if not sample_sale_id:
            pytest.skip("No sales in database")
        
        response = api_client.get(f"{BASE_URL}/api/sales/{sample_sale_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Sale should have id"

    def test_get_sale_invoice_pdf(self, api_client, sample_sale_id):
        """GET /api/sales/{id}/invoice-pdf - should return invoice HTML"""
        if not sample_sale_id:
            pytest.skip("No sales in database")
        
        response = api_client.get(f"{BASE_URL}/api/sales/{sample_sale_id}/invoice-pdf")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Should return HTML content
        content = response.text
        assert "<html" in content.lower() or "<!doctype" in content.lower() or "<div" in content.lower(), "Should return HTML content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
