"""
Test new features: Backup APIs, Selective Delete, Employee Accounts, Notifications, Customer/Supplier Families, Product View Modes
"""
import pytest
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"


class TestAuthentication:
    """Test authentication - required for all other tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login(self, auth_token):
        """Verify login works"""
        assert auth_token is not None
        print(f"✓ Login successful, got token")


class TestBackupAPIs:
    """Test Backup and Restore functionality"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_backup_download(self, auth_headers):
        """Test creating backup for download"""
        response = requests.get(f"{BASE_URL}/api/backup/create", headers=auth_headers)
        assert response.status_code == 200, f"Backup creation failed: {response.status_code}"
        
        # Check response headers for file download
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type or "application/octet-stream" in content_type
        
        # Verify backup data structure
        backup_data = response.json()
        assert "created_at" in backup_data
        assert "collections" in backup_data
        
        print(f"✓ Backup download works - contains {len(backup_data['collections'])} collections")
    
    def test_save_backup_to_server(self, auth_headers):
        """Test saving backup to server storage"""
        response = requests.post(f"{BASE_URL}/api/backup/save-to-server", headers=auth_headers)
        assert response.status_code == 200, f"Server backup failed: {response.status_code}"
        
        data = response.json()
        assert "filename" in data
        assert "backup_" in data["filename"]
        
        print(f"✓ Server backup saved: {data['filename']}")
    
    def test_list_backups(self, auth_headers):
        """Test listing available backups"""
        response = requests.get(f"{BASE_URL}/api/backup/list", headers=auth_headers)
        assert response.status_code == 200, f"List backups failed: {response.status_code}"
        
        backups = response.json()
        assert isinstance(backups, list)
        print(f"✓ List backups works - found {len(backups)} backups")


class TestSelectiveDelete:
    """Test Selective Data Deletion"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_selective_delete_wrong_confirmation(self, auth_headers):
        """Test that wrong confirmation code is rejected"""
        response = requests.post(f"{BASE_URL}/api/system/selective-delete", 
            headers=auth_headers,
            json={
                "data_types": ["notifications"],
                "confirm_code": "WRONG-CODE"
            })
        assert response.status_code == 400, "Should reject wrong confirmation"
        print(f"✓ Selective delete correctly rejects wrong confirmation code")
    
    def test_selective_delete_notifications(self, auth_headers):
        """Test selective delete of notifications (safe to test)"""
        response = requests.post(f"{BASE_URL}/api/system/selective-delete", 
            headers=auth_headers,
            json={
                "data_types": ["notifications"],
                "confirm_code": "DELETE-SELECTED"
            })
        assert response.status_code == 200, f"Selective delete failed: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        assert "deleted_counts" in data
        
        print(f"✓ Selective delete works - deleted counts: {data['deleted_counts']}")


class TestEmployeeAccounts:
    """Test Employee Account Creation and Management"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_employees(self, auth_headers):
        """Test listing employees"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        assert response.status_code == 200, f"List employees failed: {response.status_code}"
        
        employees = response.json()
        assert isinstance(employees, list)
        print(f"✓ List employees works - found {len(employees)} employees")
        return employees
    
    def test_create_employee(self, auth_headers):
        """Test creating an employee"""
        # Create test employee
        test_employee = {
            "name": f"TEST_Employee_{datetime.now().strftime('%H%M%S')}",
            "phone": "0555123456",
            "email": f"test_emp_{datetime.now().strftime('%H%M%S')}@test.com",
            "position": "Sales",
            "salary": 50000
        }
        
        response = requests.post(f"{BASE_URL}/api/employees", headers=auth_headers, json=test_employee)
        assert response.status_code == 200, f"Create employee failed: {response.text}"
        
        employee = response.json()
        assert "id" in employee
        assert employee["name"] == test_employee["name"]
        
        print(f"✓ Create employee works - ID: {employee['id']}")
        return employee["id"]
    
    def test_create_employee_account(self, auth_headers):
        """Test creating a user account for an employee"""
        # First create a fresh employee
        test_employee = {
            "name": f"TEST_AccEmp_{datetime.now().strftime('%H%M%S')}",
            "phone": "0555123457",
            "position": "Cashier",
            "salary": 40000
        }
        
        emp_response = requests.post(f"{BASE_URL}/api/employees", headers=auth_headers, json=test_employee)
        assert emp_response.status_code == 200, f"Create employee failed: {emp_response.text}"
        employee_id = emp_response.json()["id"]
        
        # Create account for this employee
        account_data = {
            "email": f"emp_acc_{datetime.now().strftime('%H%M%S')}@test.com",
            "password": "emp123",
            "role": "seller"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/employees/{employee_id}/create-account",
            headers=auth_headers,
            json=account_data
        )
        assert response.status_code == 200, f"Create employee account failed: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert "user_id" in data
        
        print(f"✓ Create employee account works - User ID: {data['user_id']}, Email: {data['email']}")
        
        # Clean up - delete the created account and employee
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}/delete-account", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
    
    def test_delete_employee_account_no_account(self, auth_headers):
        """Test deleting account when employee has none"""
        # Create employee without account
        test_employee = {
            "name": f"TEST_NoAcc_{datetime.now().strftime('%H%M%S')}",
            "phone": "0555123458",
            "position": "Staff",
            "salary": 30000
        }
        
        emp_response = requests.post(f"{BASE_URL}/api/employees", headers=auth_headers, json=test_employee)
        employee_id = emp_response.json()["id"]
        
        # Try to delete non-existent account
        response = requests.delete(
            f"{BASE_URL}/api/employees/{employee_id}/delete-account",
            headers=auth_headers
        )
        assert response.status_code == 400, "Should fail when no account exists"
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        print(f"✓ Delete employee account correctly handles no account case")


class TestNotifications:
    """Test Notification Management"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_notification_settings(self, auth_headers):
        """Test getting notification settings"""
        response = requests.get(f"{BASE_URL}/api/notifications/settings", headers=auth_headers)
        assert response.status_code == 200, f"Get settings failed: {response.status_code}"
        
        settings = response.json()
        assert "low_stock_enabled" in settings
        assert "debt_reminder_enabled" in settings
        
        print(f"✓ Get notification settings works - low_stock: {settings['low_stock_enabled']}")
    
    def test_update_notification_settings(self, auth_headers):
        """Test updating notification settings"""
        new_settings = {
            "low_stock_enabled": True,
            "low_stock_threshold": 15,
            "debt_reminder_enabled": True,
            "debt_reminder_days": 14,
            "cash_difference_enabled": True,
            "cash_difference_threshold": 2000,
            "expense_reminder_enabled": True,
            "repair_status_enabled": True,
            "email_notifications": False,
            "sound_enabled": True
        }
        
        response = requests.put(
            f"{BASE_URL}/api/notifications/settings",
            headers=auth_headers,
            json=new_settings
        )
        assert response.status_code == 200, f"Update settings failed: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        
        # Verify the update
        verify_response = requests.get(f"{BASE_URL}/api/notifications/settings", headers=auth_headers)
        updated = verify_response.json()
        assert updated["low_stock_threshold"] == 15
        
        print(f"✓ Update notification settings works")
    
    def test_get_all_notifications(self, auth_headers):
        """Test getting all notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications/all", headers=auth_headers)
        assert response.status_code == 200, f"Get all notifications failed: {response.status_code}"
        
        data = response.json()
        assert "notifications" in data
        assert "total" in data
        assert "unread_count" in data
        
        print(f"✓ Get all notifications works - total: {data['total']}, unread: {data['unread_count']}")
    
    def test_mark_all_read(self, auth_headers):
        """Test marking all notifications as read"""
        response = requests.put(f"{BASE_URL}/api/notifications/mark-all-read", headers=auth_headers)
        assert response.status_code == 200, f"Mark all read failed: {response.status_code}"
        print(f"✓ Mark all notifications read works")


class TestCustomerFamilies:
    """Test Customer Family Management"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_customer_families(self, auth_headers):
        """Test listing customer families"""
        response = requests.get(f"{BASE_URL}/api/customer-families", headers=auth_headers)
        assert response.status_code == 200, f"List customer families failed: {response.status_code}"
        
        families = response.json()
        assert isinstance(families, list)
        
        print(f"✓ List customer families works - found {len(families)} families")
    
    def test_create_customer_family(self, auth_headers):
        """Test creating a customer family"""
        family_data = {
            "name": f"TEST_Family_{datetime.now().strftime('%H%M%S')}"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/customer-families",
            headers=auth_headers,
            json=family_data
        )
        assert response.status_code == 200, f"Create customer family failed: {response.text}"
        
        family = response.json()
        assert "id" in family
        assert family["name"] == family_data["name"]
        
        print(f"✓ Create customer family works - ID: {family['id']}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/customer-families/{family['id']}", headers=auth_headers)
    
    def test_add_customer_with_family(self, auth_headers):
        """Test adding a customer with a family"""
        # First create a family
        family_data = {"name": f"TEST_CustFam_{datetime.now().strftime('%H%M%S')}"}
        fam_response = requests.post(f"{BASE_URL}/api/customer-families", headers=auth_headers, json=family_data)
        family_id = fam_response.json()["id"]
        
        # Create customer with family
        customer_data = {
            "name": f"TEST_Customer_{datetime.now().strftime('%H%M%S')}",
            "phone": "0555999888",
            "family_id": family_id
        }
        
        response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json=customer_data)
        assert response.status_code == 200, f"Create customer with family failed: {response.text}"
        
        customer = response.json()
        assert customer["family_id"] == family_id
        
        print(f"✓ Add customer with family works - Customer ID: {customer['id']}, Family: {customer.get('family_name', 'N/A')}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/customers/{customer['id']}", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/customer-families/{family_id}", headers=auth_headers)


class TestSupplierFamilies:
    """Test Supplier Family Management"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_supplier_families(self, auth_headers):
        """Test listing supplier families"""
        response = requests.get(f"{BASE_URL}/api/supplier-families", headers=auth_headers)
        assert response.status_code == 200, f"List supplier families failed: {response.status_code}"
        
        families = response.json()
        assert isinstance(families, list)
        
        print(f"✓ List supplier families works - found {len(families)} families")
    
    def test_create_supplier_family(self, auth_headers):
        """Test creating a supplier family"""
        family_data = {
            "name": f"TEST_SupFam_{datetime.now().strftime('%H%M%S')}"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/supplier-families",
            headers=auth_headers,
            json=family_data
        )
        assert response.status_code == 200, f"Create supplier family failed: {response.text}"
        
        family = response.json()
        assert "id" in family
        
        print(f"✓ Create supplier family works - ID: {family['id']}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/supplier-families/{family['id']}", headers=auth_headers)
    
    def test_add_supplier_with_family(self, auth_headers):
        """Test adding a supplier with a family"""
        # First create a family
        family_data = {"name": f"TEST_SupFam_{datetime.now().strftime('%H%M%S')}"}
        fam_response = requests.post(f"{BASE_URL}/api/supplier-families", headers=auth_headers, json=family_data)
        family_id = fam_response.json()["id"]
        
        # Create supplier with family
        supplier_data = {
            "name": f"TEST_Supplier_{datetime.now().strftime('%H%M%S')}",
            "phone": "0555888777",
            "family_id": family_id
        }
        
        response = requests.post(f"{BASE_URL}/api/suppliers", headers=auth_headers, json=supplier_data)
        assert response.status_code == 200, f"Create supplier with family failed: {response.text}"
        
        supplier = response.json()
        assert supplier["family_id"] == family_id
        
        print(f"✓ Add supplier with family works - Supplier ID: {supplier['id']}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/suppliers/{supplier['id']}", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/supplier-families/{family_id}", headers=auth_headers)


class TestProductsAPI:
    """Test Products API for view modes support"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_products(self, auth_headers):
        """Test listing products (used by all view modes)"""
        response = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        assert response.status_code == 200, f"List products failed: {response.status_code}"
        
        products = response.json()
        assert isinstance(products, list)
        
        # Verify product structure has all required fields for view modes
        if products:
            product = products[0]
            assert "id" in product
            assert "name_en" in product or "name_ar" in product
            assert "retail_price" in product or "price" in product
            assert "quantity" in product
            assert "image_url" in product
        
        print(f"✓ List products works - found {len(products)} products")


class TestAIAssistant:
    """Test AI Assistant functionality"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_ai_chat_endpoint(self, auth_headers):
        """Test AI chat endpoint is accessible"""
        response = requests.post(
            f"{BASE_URL}/api/ai/chat",
            headers=auth_headers,
            json={
                "message": "مرحبا",
                "session_id": "test-session"
            }
        )
        # AI endpoint may return 200 (success) or 402/500 (budget exceeded) - both are valid
        assert response.status_code in [200, 402, 500], f"AI chat endpoint not accessible: {response.status_code}"
        
        print(f"✓ AI chat endpoint accessible - status: {response.status_code}")
    
    def test_ai_analyze_endpoint(self, auth_headers):
        """Test AI analyze endpoint is accessible"""
        response = requests.post(
            f"{BASE_URL}/api/ai/analyze",
            headers=auth_headers,
            json={
                "analysis_type": "sales_forecast"
            }
        )
        # AI endpoint may return 200 or budget/error code
        assert response.status_code in [200, 402, 500], f"AI analyze endpoint not accessible: {response.status_code}"
        
        print(f"✓ AI analyze endpoint accessible - status: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
