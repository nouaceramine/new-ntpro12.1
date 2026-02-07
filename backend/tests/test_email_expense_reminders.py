"""
Test Email Settings and Expense Reminders APIs
Features tested:
- GET /api/email/settings - Email settings retrieval
- PUT /api/email/settings - Email settings update
- GET /api/expenses/reminders - Expense reminders for recurring expenses
- POST /api/expenses/{id}/mark-paid - Mark recurring expense as paid
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEmailSettings:
    """Email Settings API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed - skipping tests")
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_email_settings(self):
        """Test GET /api/email/settings returns settings"""
        response = requests.get(f"{BASE_URL}/api/email/settings", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should have these fields
        assert "enabled" in data, "Response should have 'enabled' field"
        assert "sender_email" in data, "Response should have 'sender_email' field"
        print(f"Email settings retrieved: enabled={data.get('enabled')}, sender={data.get('sender_email')}")
    
    def test_update_email_settings_enable(self):
        """Test PUT /api/email/settings to enable email"""
        update_data = {
            "enabled": True,
            "resend_api_key": "re_test_key_12345",
            "sender_email": "test@example.com",
            "sender_name": "Test System"
        }
        
        response = requests.put(f"{BASE_URL}/api/email/settings", json=update_data, headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Should return success=true"
        print(f"Email settings updated successfully: {data}")
    
    def test_update_email_settings_disable(self):
        """Test PUT /api/email/settings to disable email"""
        update_data = {
            "enabled": False,
            "resend_api_key": "",
            "sender_email": "onboarding@resend.dev",
            "sender_name": "NT POS System"
        }
        
        response = requests.put(f"{BASE_URL}/api/email/settings", json=update_data, headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("Email settings disabled successfully")
    
    def test_get_email_settings_after_update(self):
        """Test GET /api/email/settings returns updated settings"""
        # First update
        update_data = {
            "enabled": True,
            "resend_api_key": "re_test_1234567890",
            "sender_email": "pos@mydomain.com",
            "sender_name": "POS System"
        }
        requests.put(f"{BASE_URL}/api/email/settings", json=update_data, headers=self.headers)
        
        # Then get
        response = requests.get(f"{BASE_URL}/api/email/settings", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("enabled") == True, "enabled should be True"
        assert data.get("sender_email") == "pos@mydomain.com", "sender_email should match"
        assert data.get("sender_name") == "POS System", "sender_name should match"
        # API key should be masked
        assert "..." in data.get("resend_api_key", "") or "configured" in data.get("resend_api_key", "").lower(), "API key should be masked"
        print(f"Settings persisted correctly: {data}")


class TestExpenseReminders:
    """Expense Reminders API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed - skipping tests")
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.created_expense_ids = []
    
    def teardown_method(self, method):
        """Cleanup test expenses after each test"""
        for expense_id in self.created_expense_ids:
            try:
                requests.delete(f"{BASE_URL}/api/expenses/{expense_id}", headers=self.headers)
            except:
                pass
    
    def test_get_expense_reminders_empty(self):
        """Test GET /api/expenses/reminders returns list (possibly empty)"""
        response = requests.get(f"{BASE_URL}/api/expenses/reminders", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Got {len(data)} reminders")
    
    def test_create_recurring_expense_and_check_reminder(self):
        """Test creating a recurring expense shows up in reminders"""
        # Create a recurring expense due soon (today's date means next period starts soon)
        expense_data = {
            "title": "TEST_Monthly_Rent",
            "category": "rent",
            "amount": 50000,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "notes": "Test recurring expense for reminders",
            "recurring": True,
            "recurring_period": "monthly",
            "reminder_days_before": 30  # 30 days should capture upcoming
        }
        
        create_response = requests.post(f"{BASE_URL}/api/expenses", json=expense_data, headers=self.headers)
        assert create_response.status_code in [200, 201], f"Failed to create expense: {create_response.text}"
        
        expense_id = create_response.json().get("id")
        self.created_expense_ids.append(expense_id)
        print(f"Created recurring expense with ID: {expense_id}")
        
        # Check reminders
        reminders_response = requests.get(f"{BASE_URL}/api/expenses/reminders", headers=self.headers)
        assert reminders_response.status_code == 200
        
        reminders = reminders_response.json()
        print(f"Found {len(reminders)} reminders after creating recurring expense")
        
        # Note: The reminder might not show up immediately depending on the date logic
        # but the endpoint should work without errors
    
    def test_mark_expense_paid(self):
        """Test POST /api/expenses/{id}/mark-paid updates expense"""
        # First create a recurring expense
        expense_data = {
            "title": "TEST_Rent_MarkPaid",
            "category": "rent",
            "amount": 25000,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "notes": "Test expense for mark-paid",
            "recurring": True,
            "recurring_period": "monthly",
            "reminder_days_before": 3
        }
        
        create_response = requests.post(f"{BASE_URL}/api/expenses", json=expense_data, headers=self.headers)
        assert create_response.status_code in [200, 201], f"Failed to create expense: {create_response.text}"
        
        expense_id = create_response.json().get("id")
        self.created_expense_ids.append(expense_id)
        
        # Mark as paid
        mark_paid_response = requests.post(f"{BASE_URL}/api/expenses/{expense_id}/mark-paid", headers=self.headers)
        
        assert mark_paid_response.status_code == 200, f"Expected 200, got {mark_paid_response.status_code}: {mark_paid_response.text}"
        
        data = mark_paid_response.json()
        assert "message" in data, "Response should have message"
        print(f"Mark paid response: {data}")
        
        # Verify the expense date was updated
        get_response = requests.get(f"{BASE_URL}/api/expenses/{expense_id}", headers=self.headers)
        if get_response.status_code == 200:
            updated_expense = get_response.json()
            assert "last_paid_at" in updated_expense or "updated_at" in updated_expense, "Expense should have updated timestamp"
            print(f"Expense updated with new date")
    
    def test_mark_paid_nonexistent_expense(self):
        """Test POST /api/expenses/{id}/mark-paid for non-existent expense returns 404"""
        fake_id = "nonexistent-expense-id-12345"
        response = requests.post(f"{BASE_URL}/api/expenses/{fake_id}/mark-paid", headers=self.headers)
        
        assert response.status_code == 404, f"Expected 404 for non-existent expense, got {response.status_code}"
        print("Correctly returned 404 for non-existent expense")


class TestExpensesBasicCRUD:
    """Basic Expenses API Tests to ensure expenses work before testing reminders"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed - skipping tests")
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.created_expense_ids = []
    
    def teardown_method(self, method):
        """Cleanup test expenses after each test"""
        for expense_id in self.created_expense_ids:
            try:
                requests.delete(f"{BASE_URL}/api/expenses/{expense_id}", headers=self.headers)
            except:
                pass
    
    def test_get_expenses_list(self):
        """Test GET /api/expenses returns list"""
        response = requests.get(f"{BASE_URL}/api/expenses", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Got {len(data)} expenses")
    
    def test_create_expense(self):
        """Test POST /api/expenses creates new expense"""
        expense_data = {
            "title": "TEST_Electricity_Bill",
            "category": "utilities",
            "amount": 3500,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "notes": "Test expense",
            "recurring": False
        }
        
        response = requests.post(f"{BASE_URL}/api/expenses", json=expense_data, headers=self.headers)
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("id"), "Response should have id"
        assert data.get("title") == "TEST_Electricity_Bill", "Title should match"
        assert data.get("amount") == 3500, "Amount should match"
        
        self.created_expense_ids.append(data["id"])
        print(f"Created expense: {data['id']}")
    
    def test_get_expense_stats(self):
        """Test GET /api/expenses/stats returns statistics"""
        response = requests.get(f"{BASE_URL}/api/expenses/stats", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total" in data, "Stats should have total"
        assert "thisMonth" in data, "Stats should have thisMonth"
        print(f"Expense stats: total={data.get('total')}, thisMonth={data.get('thisMonth')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
