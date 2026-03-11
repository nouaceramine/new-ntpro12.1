"""
Test iteration 57 - New features testing
- Tax Reports API (/api/tax/*)
- Currencies API (/api/currencies/*)
- WhatsApp API (/api/whatsapp/*)
- Notifications API (/api/notifications/*)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN = {"email": "admin@ntcommerce.com", "password": "Admin@2024"}
TENANT = {"email": "ncr@ntcommerce.com", "password": "Test@123"}


class TestAuthentication:
    """Test authentication endpoints for unified-login"""
    
    def test_tenant_login(self):
        """Test tenant login via unified-login endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/auth/unified-login",
            json=TENANT
        )
        print(f"Tenant login status: {response.status_code}")
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print(f"Tenant login SUCCESS - token received")
        return data["access_token"]
    
    def test_super_admin_login(self):
        """Test super admin login via unified-login endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/auth/unified-login",
            json=SUPER_ADMIN
        )
        print(f"Super Admin login status: {response.status_code}")
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print(f"Super Admin login SUCCESS - token received")
        return data["access_token"]


class TestTaxRatesAPI:
    """Test /api/tax/rates endpoints"""
    
    @pytest.fixture(scope="class")
    def tenant_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_tax_rates(self, tenant_token):
        """GET /api/tax/rates - should return 5 default rates"""
        response = requests.get(
            f"{BASE_URL}/api/tax/rates",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/tax/rates: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 5, f"Expected at least 5 rates, got {len(data)}"
        
        # Check for default rates
        rate_names = [r.get("name") for r in data]
        print(f"Tax rates found: {rate_names}")
        assert "VAT Standard" in rate_names or any("ضريبة" in r.get("name_ar", "") for r in data)
        print("Tax rates API working correctly")
    
    def test_create_tax_rate(self, tenant_token):
        """POST /api/tax/rates - create a new rate"""
        new_rate = {
            "name": "TEST_Custom Tax",
            "name_ar": "ضريبة مخصصة للاختبار",
            "rate": 5.5,
            "type": "withholding",
            "is_active": True
        }
        response = requests.post(
            f"{BASE_URL}/api/tax/rates",
            json=new_rate,
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"POST /api/tax/rates: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == new_rate["name"]
        print(f"Created tax rate with id: {data['id']}")
        return data["id"]


class TestTaxReportAPI:
    """Test /api/tax/report endpoint"""
    
    @pytest.fixture(scope="class")
    def tenant_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_generate_tax_report(self, tenant_token):
        """GET /api/tax/report - generate tax report"""
        response = requests.get(
            f"{BASE_URL}/api/tax/report",
            params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/tax/report: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify report structure
        required_fields = ["period", "total_sales", "vat_collected", "vat_paid", "vat_due", "taxable_income"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"Tax report: VAT Due={data['vat_due']}, Income Tax={data.get('income_tax', 0)}")
        print("Tax report generation working correctly")


class TestCurrenciesAPI:
    """Test /api/currencies/* endpoints"""
    
    @pytest.fixture(scope="class")
    def tenant_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_currencies(self, tenant_token):
        """GET /api/currencies/ - should return 10 currencies"""
        response = requests.get(
            f"{BASE_URL}/api/currencies/",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/currencies/: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 10, f"Expected at least 10 currencies, got {len(data)}"
        
        # Check for key currencies
        codes = [c.get("code") for c in data]
        print(f"Currencies found: {codes}")
        expected_codes = ["DZD", "USD", "EUR", "GBP", "SAR"]
        for code in expected_codes:
            assert code in codes, f"Missing currency: {code}"
        print("Currencies API working correctly")
    
    def test_convert_currency(self, tenant_token):
        """POST /api/currencies/convert - convert DZD to USD"""
        response = requests.post(
            f"{BASE_URL}/api/currencies/convert",
            json={"amount": 1000, "from_currency": "DZD", "to_currency": "USD"},
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"POST /api/currencies/convert: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        
        assert "converted_amount" in data
        assert "rate" in data
        assert data["from"] == "DZD"
        assert data["to"] == "USD"
        print(f"Currency conversion: 1000 DZD = {data['converted_amount']} USD (rate: {data['rate']})")
        print("Currency conversion working correctly")
    
    def test_get_currency_settings(self, tenant_token):
        """GET /api/currencies/settings - get settings"""
        response = requests.get(
            f"{BASE_URL}/api/currencies/settings",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/currencies/settings: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert "default_currency" in data
        print(f"Currency settings: default={data.get('default_currency')}")


class TestWhatsAppAPI:
    """Test /api/whatsapp/* endpoints"""
    
    @pytest.fixture(scope="class")
    def tenant_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_whatsapp_config(self, tenant_token):
        """GET /api/whatsapp/config - get config"""
        response = requests.get(
            f"{BASE_URL}/api/whatsapp/config",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/whatsapp/config: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        
        assert "tenant_id" in data
        assert "is_active" in data
        assert "verify_token" in data
        print(f"WhatsApp config: active={data.get('is_active')}, auto_reply={data.get('auto_reply')}")
        print("WhatsApp config API working correctly")
    
    def test_get_whatsapp_messages(self, tenant_token):
        """GET /api/whatsapp/messages - get messages"""
        response = requests.get(
            f"{BASE_URL}/api/whatsapp/messages",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/whatsapp/messages: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"WhatsApp messages count: {len(data)}")
    
    def test_get_whatsapp_stats(self, tenant_token):
        """GET /api/whatsapp/stats - get stats"""
        response = requests.get(
            f"{BASE_URL}/api/whatsapp/stats",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/whatsapp/stats: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        
        assert "incoming" in data
        assert "outgoing" in data
        assert "total" in data
        assert "is_active" in data
        print(f"WhatsApp stats: in={data['incoming']}, out={data['outgoing']}, total={data['total']}")
        print("WhatsApp stats API working correctly")


class TestNotificationsAPI:
    """Test /api/notifications/* endpoints"""
    
    @pytest.fixture(scope="class")
    def tenant_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_unread_count(self, tenant_token):
        """GET /api/notifications/unread-count - get unread count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/notifications/unread-count: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        print(f"Unread notifications count: {data['count']}")
        print("Notifications unread-count API working correctly")
    
    def test_get_notifications(self, tenant_token):
        """GET /api/notifications/ - get notifications list"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/notifications/: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Notifications count: {len(data)}")
    
    def test_get_notification_preferences(self, tenant_token):
        """GET /api/notifications/preferences - get preferences"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/preferences",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/notifications/preferences: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert "low_stock_alert" in data or "daily_summary" in data
        print(f"Notification preferences loaded")


class TestTaxDeclarationsAPI:
    """Test /api/tax/declarations endpoints"""
    
    @pytest.fixture(scope="class")
    def tenant_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_declarations(self, tenant_token):
        """GET /api/tax/declarations - get declarations list"""
        response = requests.get(
            f"{BASE_URL}/api/tax/declarations",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/tax/declarations: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Tax declarations count: {len(data)}")
    
    def test_get_annual_summary(self, tenant_token):
        """GET /api/tax/summary/2026 - get annual summary"""
        response = requests.get(
            f"{BASE_URL}/api/tax/summary/2026",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        print(f"GET /api/tax/summary/2026: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        
        assert "year" in data
        assert "quarterly" in data
        assert "annual" in data
        assert isinstance(data["quarterly"], list)
        print(f"Annual summary for {data['year']}: Total sales={data['annual'].get('total_sales', 0)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
