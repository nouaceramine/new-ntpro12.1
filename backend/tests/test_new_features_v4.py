"""
Test New Features v4 - Price History, Smart Reports, Employee Alerts
Testing the new 4 features added to the inventory/sales app
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Test login to get token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_success(self):
        """Test that login works with provided credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"Login successful, user role: {data['user']['role']}")


class TestPriceHistoryAPI:
    """Test Price History API endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_get_all_price_history(self, auth_token):
        """Test GET /api/price-history - Get all price change history"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/price-history?limit=50", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Price history: Found {len(data)} records")
        
        # If there's data, verify structure
        if len(data) > 0:
            record = data[0]
            assert "id" in record
            assert "product_id" in record
            assert "product_name" in record
            assert "old_price" in record
            assert "new_price" in record
            assert "price_type" in record
            assert "change_percent" in record
            print(f"First record: {record['product_name']} - {record['old_price']} -> {record['new_price']} ({record['change_percent']}%)")
    
    def test_get_price_history_with_filter(self, auth_token):
        """Test GET /api/price-history with price_type filter"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test filter by purchase_price
        response = requests.get(f"{BASE_URL}/api/price-history?price_type=purchase_price&limit=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Price history filtered by purchase_price: {len(data)} records")
        
        # Test filter by retail_price
        response = requests.get(f"{BASE_URL}/api/price-history?price_type=retail_price&limit=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Price history filtered by retail_price: {len(data)} records")


class TestSmartReportsAPI:
    """Test Smart Reports API endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_get_smart_report_settings(self, auth_token):
        """Test GET /api/smart-reports/settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/smart-reports/settings", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify expected fields
        assert "daily_report_enabled" in data
        assert "daily_report_time" in data
        assert "daily_report_recipients" in data
        assert "include_ai_tips" in data
        assert "include_sales_summary" in data
        assert "include_low_stock_alerts" in data
        assert "include_debt_reminders" in data
        
        print(f"Smart report settings: enabled={data['daily_report_enabled']}, time={data['daily_report_time']}")
    
    def test_get_smart_report_preview(self, auth_token):
        """Test GET /api/smart-reports/preview"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/smart-reports/preview", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify expected structure
        assert "sales" in data
        assert "low_stock" in data
        assert "ai_tips" in data
        
        # Verify sales summary structure
        sales = data["sales"]
        assert "today_total" in sales
        assert "today_count" in sales
        assert "today_profit" in sales
        assert "change" in sales
        
        print(f"Report preview - Sales today: {sales['today_total']}, Count: {sales['today_count']}")
        print(f"Low stock items: {len(data['low_stock'])}")
        print(f"AI Tips: {data['ai_tips'][:100]}...")
    
    def test_get_last_smart_report(self, auth_token):
        """Test GET /api/smart-reports/last"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/smart-reports/last", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Can be null if no report has been sent yet
        if data:
            print(f"Last report: sent at {data.get('sent_at')}")
        else:
            print("No reports sent yet")
    
    def test_update_smart_report_settings(self, auth_token):
        """Test PUT /api/smart-reports/settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get current settings
        response = requests.get(f"{BASE_URL}/api/smart-reports/settings", headers=headers)
        current = response.json()
        
        # Update settings
        new_settings = {
            "daily_report_enabled": current.get("daily_report_enabled", False),
            "daily_report_time": "09:00",
            "daily_report_recipients": current.get("daily_report_recipients", ""),
            "include_ai_tips": True,
            "include_sales_summary": True,
            "include_low_stock_alerts": True,
            "include_debt_reminders": True
        }
        
        response = requests.put(f"{BASE_URL}/api/smart-reports/settings", 
                               json=new_settings, headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print("Smart report settings updated successfully")


class TestEmployeeAlertsAPI:
    """Test Employee Alerts API endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_get_employees_list(self, auth_token):
        """Test GET /api/employees - Get list of employees"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/employees", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} employees")
        
        # Return first employee ID for further tests
        return data[0]["id"] if data else None
    
    def test_get_active_employee_alerts(self, auth_token):
        """Test GET /api/employees/alerts/active"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/employees/alerts/active", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        
        print(f"Active employee alerts: {len(data)}")
        
        # If there are alerts, verify structure
        if len(data) > 0:
            alert = data[0]
            assert "type" in alert
            assert "severity" in alert
            assert "employee_id" in alert
            assert "employee_name" in alert
            print(f"First alert: {alert['type']} - {alert['employee_name']} ({alert['severity']})")
    
    def test_get_employee_alert_settings(self, auth_token):
        """Test GET /api/employees/{id}/alert-settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get an employee
        emp_response = requests.get(f"{BASE_URL}/api/employees", headers=headers)
        employees = emp_response.json()
        
        if not employees:
            pytest.skip("No employees found to test alert settings")
        
        emp_id = employees[0]["id"]
        response = requests.get(f"{BASE_URL}/api/employees/{emp_id}/alert-settings", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify expected fields
        assert "employee_id" in data
        assert "enable_discount_alert" in data
        assert "discount_threshold_percent" in data
        assert "enable_debt_alert" in data
        assert "debt_threshold_percent" in data
        
        print(f"Employee {emp_id} alert settings: discount_alert={data['enable_discount_alert']}, debt_alert={data['enable_debt_alert']}")


class TestWarehouseAPI:
    """Test Warehouse selection for POS"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_get_warehouses(self, auth_token):
        """Test GET /api/warehouses - Verify warehouse selection is available"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/warehouses", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        
        print(f"Found {len(data)} warehouses")
        
        # If there are warehouses, verify structure
        if len(data) > 0:
            wh = data[0]
            assert "id" in wh
            assert "name" in wh
            assert "is_main" in wh
            print(f"First warehouse: {wh['name']} (main: {wh['is_main']})")


class TestEmailSettings:
    """Test Email Settings API (required for smart reports)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_get_email_settings(self, auth_token):
        """Test GET /api/email/settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/email/settings", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify expected fields
        assert "enabled" in data
        print(f"Email settings: enabled={data.get('enabled')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
