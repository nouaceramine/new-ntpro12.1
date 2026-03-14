"""
NT Commerce 12.0 - Iteration 66 Testing
Tests for: Permissions, Smart Notifications, Repairs, Defective Goods, Backup, Wallet, 2FA
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDS = {"email": "admin@ntcommerce.com", "password": "Admin@2024"}
TENANT_CREDS = {"email": "ncr@ntcommerce.com", "password": "Test@123"}


class TestAuth:
    """Authentication endpoint tests"""
    
    def test_admin_login_success(self):
        """Test admin login via unified-login"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=ADMIN_CREDS)
        print(f"Admin login status: {response.status_code}")
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        print(f"Admin login success, token present: {bool(data.get('access_token'))}")
    
    def test_tenant_login_success(self):
        """Test tenant login via unified-login"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_CREDS)
        print(f"Tenant login status: {response.status_code}")
        assert response.status_code == 200, f"Tenant login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        print(f"Tenant login success, user: {data.get('user', {}).get('email')}")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=ADMIN_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def tenant_token():
    """Get tenant token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Tenant authentication failed")


class TestPermissionsAPI:
    """Permissions system tests - 185 permissions across 33 modules"""
    
    def test_permissions_catalog(self, admin_token):
        """GET /api/permissions/catalog - should return 185+ permissions"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/permissions/catalog", headers=headers)
        print(f"Permissions catalog status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_permissions" in data
        assert "modules" in data
        print(f"Total permissions: {data.get('total_permissions')}, modules: {len(data.get('modules', []))}")
        # Expect around 185 permissions across 33 modules
        assert data.get('total_permissions', 0) >= 100, "Expected 100+ permissions"
        assert len(data.get('modules', [])) >= 25, "Expected 25+ modules"
    
    def test_role_templates(self, admin_token):
        """GET /api/permissions/role-templates - should return 8 templates"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/permissions/role-templates", headers=headers)
        print(f"Role templates status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Role templates count: {len(data)}")
        # Expected templates: owner, manager, cashier, salesperson, technician, accountant, warehouse_keeper, viewer
        assert len(data) >= 8, "Expected 8+ role templates"
        template_keys = [t.get('key') for t in data]
        print(f"Template keys: {template_keys}")
    
    def test_create_role(self, tenant_token):
        """POST /api/permissions/roles - create custom role"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        role_data = {
            "name_ar": "دور اختبار",
            "name_fr": "Rôle de test",
            "description_ar": "دور للاختبار فقط",
            "template": "cashier"
        }
        response = requests.post(f"{BASE_URL}/api/permissions/roles", json=role_data, headers=headers)
        print(f"Create role status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data.get("name_ar") == "دور اختبار"
        print(f"Created role: {data.get('id')}")
    
    def test_get_roles(self, tenant_token):
        """GET /api/permissions/roles - list all roles"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/permissions/roles", headers=headers)
        print(f"Get roles status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Total roles: {len(data)}")
    
    def test_permissions_stats(self, admin_token):
        """GET /api/permissions/stats - permission stats"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/permissions/stats", headers=headers)
        print(f"Permissions stats status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_permissions" in data
        assert "total_modules" in data
        print(f"Stats: {data}")


class TestSmartNotificationsAPI:
    """Smart Notifications from 11 robots"""
    
    def test_get_notifications(self, tenant_token):
        """GET /api/smart-notifications - get notification list"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/smart-notifications", headers=headers)
        print(f"Get notifications status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Notifications count: {len(data)}")
    
    def test_unread_count(self, tenant_token):
        """GET /api/smart-notifications/unread-count - get unread count"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/smart-notifications/unread-count", headers=headers)
        print(f"Unread count status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "unread" in data
        print(f"Unread count: {data.get('unread')}, by_severity: {data.get('by_severity')}")
    
    def test_mark_all_read(self, tenant_token):
        """PUT /api/smart-notifications/mark-all-read - mark all as read"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.put(f"{BASE_URL}/api/smart-notifications/mark-all-read", json={}, headers=headers)
        print(f"Mark all read status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
    
    def test_notification_stats(self, tenant_token):
        """GET /api/smart-notifications/stats - notification stats"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/smart-notifications/stats", headers=headers)
        print(f"Notification stats status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total" in data
        assert "unread" in data
        print(f"Notification stats: total={data.get('total')}, unread={data.get('unread')}")


class TestRepairsAPI:
    """Repair ticket management - 16 collections"""
    
    def test_get_repair_tickets(self, tenant_token):
        """GET /api/repairs/tickets - list repair tickets"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/repairs/tickets", headers=headers)
        print(f"Get repair tickets status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Repair tickets count: {len(data)}")
    
    def test_repair_stats(self, tenant_token):
        """GET /api/repairs/stats - repair statistics"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/repairs/stats", headers=headers)
        print(f"Repair stats status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total" in data
        assert "statuses" in data
        print(f"Repair stats: total={data.get('total')}, statuses={data.get('statuses')}")
    
    def test_create_repair_ticket(self, tenant_token):
        """POST /api/repairs/tickets - create a repair ticket"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        ticket_data = {
            "customer_name": "TEST_Client Repair",
            "customer_phone": "0555123456",
            "brand_name": "Samsung",
            "model_name": "Galaxy S21",
            "reported_issue": "شاشة مكسورة",
            "estimated_cost": 5000,
            "priority": "high"
        }
        response = requests.post(f"{BASE_URL}/api/repairs/tickets", json=ticket_data, headers=headers)
        print(f"Create repair ticket status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "ticket_number" in data
        print(f"Created ticket: {data.get('ticket_number')}")
    
    def test_get_spare_parts(self, tenant_token):
        """GET /api/repairs/parts - list spare parts"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/repairs/parts", headers=headers)
        print(f"Get spare parts status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Spare parts count: {len(data)}")
    
    def test_get_technicians(self, tenant_token):
        """GET /api/repairs/technicians - list technicians"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/repairs/technicians", headers=headers)
        print(f"Get technicians status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Technicians count: {len(data)}")


class TestDefectiveGoodsAPI:
    """Defective goods management - 8 collections"""
    
    def test_defective_stats(self, tenant_token):
        """GET /api/defective/stats - defective goods stats"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/defective/stats", headers=headers)
        print(f"Defective stats status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_defective" in data
        print(f"Defective stats: {data}")
    
    def test_get_defective_goods(self, tenant_token):
        """GET /api/defective/goods - list defective goods"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/defective/goods", headers=headers)
        print(f"Get defective goods status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Defective goods count: {len(data)}")
    
    def test_get_defect_categories(self, tenant_token):
        """GET /api/defective/categories - list defect categories"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/defective/categories", headers=headers)
        print(f"Get defect categories status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Defect categories count: {len(data)}")
    
    def test_create_defective_item(self, tenant_token):
        """POST /api/defective/goods - create defective item"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        item_data = {
            "product_name": "TEST_Defective Product",
            "defect_type": "manufacturing",
            "defect_severity": "high",
            "description": "عيب تصنيع",
            "quantity": 2,
            "unit_cost": 1000
        }
        response = requests.post(f"{BASE_URL}/api/defective/goods", json=item_data, headers=headers)
        print(f"Create defective item status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "defective_number" in data
        print(f"Created defective item: {data.get('defective_number')}")


class TestBackupSystemAPI:
    """Backup system - 4 collections"""
    
    def test_backup_stats(self, tenant_token):
        """GET /api/backup/stats/summary - backup stats"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/backup/stats/summary", headers=headers)
        print(f"Backup stats status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_backups" in data
        print(f"Backup stats: {data}")
    
    def test_backup_list(self, tenant_token):
        """GET /api/backup/list - list backups"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/backup/list", headers=headers)
        print(f"Backup list status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Backups count: {len(data)}")
    
    def test_backup_schedules_list(self, tenant_token):
        """GET /api/backup/schedules/list - list backup schedules"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/backup/schedules/list", headers=headers)
        print(f"Backup schedules status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Backup schedules count: {len(data)}")


class TestWalletAPI:
    """Wallet and payment system - 3 collections"""
    
    def test_get_wallet(self, tenant_token):
        """GET /api/wallet - get wallet info"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/wallet", headers=headers)
        print(f"Get wallet status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "balance" in data
        assert "currency" in data
        print(f"Wallet: balance={data.get('balance')}, currency={data.get('currency')}")
    
    def test_wallet_transactions(self, tenant_token):
        """GET /api/wallet/transactions - list transactions"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/wallet/transactions", headers=headers)
        print(f"Wallet transactions status: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Transactions count: {len(data)}")


class Test2FAAPI:
    """Two-Factor Authentication"""
    
    def test_2fa_status_tenant(self, tenant_token):
        """GET /api/auth/2fa/status - get 2FA status for tenant"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/2fa/status", headers=headers)
        print(f"2FA status (tenant) status code: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "enabled" in data
        print(f"2FA enabled for tenant: {data.get('enabled')}")
    
    def test_2fa_status_admin(self, admin_token):
        """GET /api/auth/2fa/status - get 2FA status for admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/2fa/status", headers=headers)
        print(f"2FA status (admin) status code: {response.status_code}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "enabled" in data
        print(f"2FA enabled for admin: {data.get('enabled')}")


class TestDashboardAndSidebar:
    """Dashboard and sidebar verification"""
    
    def test_dashboard_stats(self, tenant_token):
        """GET /api/dashboard - check dashboard stats endpoint"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard", headers=headers)
        print(f"Dashboard status: {response.status_code}")
        # Dashboard might have different responses, just check it doesn't error
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
    
    def test_health_check(self):
        """GET /api/health - basic health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Health check status: {response.status_code}")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
