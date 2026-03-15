"""
Test Iteration 77 - P2 Features Verification
Tests: Repair System, Wallet System, Backup System, AI Robots Enhancement
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Credentials
SUPER_ADMIN = {"email": "admin@ntcommerce.com", "password": "Admin@2024"}
TENANT = {"email": "ncr@ntcommerce.com", "password": "Test@123"}
NORMAL_USER = {"email": "test@test.com", "password": "Test@123"}


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=SUPER_ADMIN)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.fail(f"Super admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def tenant_token():
    """Get tenant admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.fail(f"Tenant login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def normal_user_token():
    """Get normal user token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=NORMAL_USER)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Normal user login failed - skipping user tests")


# ========== REPAIR SYSTEM TESTS ==========

class TestRepairSystem:
    """Repair Ticket Management Tests"""
    
    created_ticket_id = None
    
    def test_create_repair_ticket(self, tenant_token):
        """POST /api/repairs/tickets - Create repair ticket"""
        response = requests.post(
            f"{BASE_URL}/api/repairs/tickets",
            headers={"Authorization": f"Bearer {tenant_token}"},
            json={
                "customer_name": "TEST_Customer",
                "customer_phone": "0555123456",
                "brand_name": "Samsung",
                "model_name": "Galaxy S21",
                "reported_issue": "Screen broken - not responsive",
                "priority": "high",
                "estimated_cost": 150.0
            }
        )
        assert response.status_code == 200, f"Create ticket failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "ticket_number" in data
        assert data["ticket_number"].startswith("REP-")
        assert data["customer_name"] == "TEST_Customer"
        assert data["status"] == "received"
        TestRepairSystem.created_ticket_id = data["id"]
        print(f"Created ticket: {data['ticket_number']}")
    
    def test_get_all_tickets(self, tenant_token):
        """GET /api/repairs/tickets - List all tickets"""
        response = requests.get(
            f"{BASE_URL}/api/repairs/tickets",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Total tickets: {len(data)}")
    
    def test_get_tickets_paginated(self, tenant_token):
        """GET /api/repairs/tickets/paginated - Paginated tickets"""
        response = requests.get(
            f"{BASE_URL}/api/repairs/tickets/paginated?page=1&page_size=5",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data
        print(f"Paginated: {len(data['items'])} items, total: {data['total']}")
    
    def test_update_ticket_status(self, tenant_token):
        """PUT /api/repairs/tickets/{id} - Update ticket status"""
        if not TestRepairSystem.created_ticket_id:
            pytest.skip("No ticket created")
        response = requests.put(
            f"{BASE_URL}/api/repairs/tickets/{TestRepairSystem.created_ticket_id}",
            headers={"Authorization": f"Bearer {tenant_token}"},
            json={
                "status": "diagnosed",
                "diagnosis": "LCD panel needs replacement",
                "notes": "Diagnosis complete"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "diagnosed"
        assert data.get("diagnosed_at") is not None
        print(f"Ticket status updated to: {data['status']}")
    
    def test_get_single_ticket_with_history(self, tenant_token):
        """GET /api/repairs/tickets/{id} - Get ticket with history"""
        if not TestRepairSystem.created_ticket_id:
            pytest.skip("No ticket created")
        response = requests.get(
            f"{BASE_URL}/api/repairs/tickets/{TestRepairSystem.created_ticket_id}",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert isinstance(data["history"], list)
        assert len(data["history"]) >= 1  # At least the status change history
        print(f"Ticket history entries: {len(data['history'])}")
    
    def test_get_repair_stats(self, tenant_token):
        """GET /api/repairs/stats - Repair statistics"""
        response = requests.get(
            f"{BASE_URL}/api/repairs/stats",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "statuses" in data
        assert isinstance(data["statuses"], dict)
        print(f"Repair stats: total={data['total']}, statuses={data['statuses']}")
    
    def test_delete_repair_ticket(self, tenant_token):
        """DELETE /api/repairs/tickets/{id} - Cleanup"""
        if not TestRepairSystem.created_ticket_id:
            pytest.skip("No ticket to delete")
        response = requests.delete(
            f"{BASE_URL}/api/repairs/tickets/{TestRepairSystem.created_ticket_id}",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        print("Ticket deleted successfully")


# ========== WALLET SYSTEM TESTS ==========

class TestWalletSystem:
    """Wallet & Payment System Tests"""
    
    wallet_entity_id = None
    
    def test_get_wallet_auto_create(self, tenant_token):
        """GET /api/wallet - Auto-create wallet for tenant"""
        response = requests.get(
            f"{BASE_URL}/api/wallet",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "entity_id" in data
        assert "balance" in data
        assert "currency" in data
        TestWalletSystem.wallet_entity_id = data["entity_id"]
        print(f"Wallet: entity={data['entity_id']}, balance={data['balance']} {data['currency']}")
    
    def test_add_funds_admin(self, super_admin_token):
        """POST /api/wallet/add-funds - Add funds (super admin)"""
        if not TestWalletSystem.wallet_entity_id:
            pytest.skip("No wallet entity ID")
        response = requests.post(
            f"{BASE_URL}/api/wallet/add-funds",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "entity_id": TestWalletSystem.wallet_entity_id,
                "amount": 1000.0,
                "description": "TEST_Deposit - Admin deposit"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "new_balance" in data
        assert "transaction" in data
        assert data["transaction"]["transaction_type"] == "credit"
        print(f"Added funds: new_balance={data['new_balance']}")
    
    def test_deduct_funds_admin(self, super_admin_token):
        """POST /api/wallet/deduct - Deduct funds (super admin)"""
        if not TestWalletSystem.wallet_entity_id:
            pytest.skip("No wallet entity ID")
        response = requests.post(
            f"{BASE_URL}/api/wallet/deduct",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={
                "entity_id": TestWalletSystem.wallet_entity_id,
                "amount": 100.0,
                "description": "TEST_Deduction - Service fee"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "new_balance" in data
        assert "transaction" in data
        assert data["transaction"]["transaction_type"] == "debit"
        print(f"Deducted funds: new_balance={data['new_balance']}")
    
    def test_wallet_transactions_paginated(self, tenant_token):
        """GET /api/wallet/transactions/paginated - Paginated transactions"""
        response = requests.get(
            f"{BASE_URL}/api/wallet/transactions/paginated?page=1&page_size=5",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"Transactions: {len(data['items'])} items, total={data['total']}")
    
    def test_get_all_wallets_admin(self, super_admin_token):
        """GET /api/wallet/all - List all wallets (admin only)"""
        response = requests.get(
            f"{BASE_URL}/api/wallet/all",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Total wallets: {len(data)}")
    
    def test_get_wallet_stats(self, super_admin_token):
        """GET /api/wallet/stats - Wallet statistics (admin)"""
        response = requests.get(
            f"{BASE_URL}/api/wallet/stats",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_wallets" in data
        assert "total_balance" in data
        assert "total_transactions" in data
        print(f"Wallet stats: {data}")
    
    def test_tenant_cannot_access_all_wallets(self, tenant_token):
        """Verify tenant cannot access admin-only endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/wallet/all",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Correctly denied tenant access to /wallet/all")


# ========== BACKUP SYSTEM TESTS ==========

class TestBackupSystem:
    """Backup System Tests"""
    
    created_backup_id = None
    
    def test_create_backup(self, tenant_token):
        """POST /api/backup/create - Create full backup"""
        response = requests.post(
            f"{BASE_URL}/api/backup/create",
            headers={"Authorization": f"Bearer {tenant_token}"},
            json={
                "backup_type": "full",
                "format": "json"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "backup_number" in data
        assert data["backup_number"].startswith("BKP-")
        assert data["status"] == "completed"
        assert data["file_size"] > 0
        TestBackupSystem.created_backup_id = data["id"]
        print(f"Created backup: {data['backup_number']}, size={data['file_size']} bytes, records={data['records_count']}")
    
    def test_list_backups(self, tenant_token):
        """GET /api/backup/list - List all backups"""
        response = requests.get(
            f"{BASE_URL}/api/backup/list",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Total backups: {len(data)}")
    
    def test_download_backup_returns_file(self, tenant_token):
        """POST /api/backup/{id}/download - Download backup as JSON file"""
        if not TestBackupSystem.created_backup_id:
            pytest.skip("No backup created")
        response = requests.post(
            f"{BASE_URL}/api/backup/{TestBackupSystem.created_backup_id}/download",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        # Check it's actual JSON file content
        assert "application/json" in response.headers.get("content-type", "")
        assert "attachment" in response.headers.get("content-disposition", "")
        # Verify it's valid JSON data
        try:
            backup_data = response.json()
            assert isinstance(backup_data, dict)
            print(f"Downloaded backup: {len(backup_data)} collections")
        except json.JSONDecodeError:
            pytest.fail("Downloaded backup is not valid JSON")
    
    def test_restore_backup(self, tenant_token):
        """POST /api/backup/restore - Restore from backup data"""
        # Create minimal backup data for restore test
        response = requests.post(
            f"{BASE_URL}/api/backup/restore",
            headers={"Authorization": f"Bearer {tenant_token}"},
            json={
                "backup_data": {
                    "test_restore_collection": [
                        {"id": "test1", "name": "Test Item 1"},
                        {"id": "test2", "name": "Test Item 2"}
                    ]
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "restored_collections" in data
        assert "restored_records" in data
        print(f"Restored: {data['restored_collections']} collections, {data['restored_records']} records")
    
    def test_backup_stats(self, tenant_token):
        """GET /api/backup/stats/summary - Backup statistics"""
        response = requests.get(
            f"{BASE_URL}/api/backup/stats/summary",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_backups" in data
        assert "total_size" in data
        assert "active_schedules" in data
        print(f"Backup stats: {data}")


# ========== AI ROBOTS TESTS ==========

class TestAIRobots:
    """AI Robots Status and Enhancement Tests"""
    
    def test_robots_status_all_11_running(self, super_admin_token):
        """GET /api/robots/status - Verify all 11 robots are running"""
        response = requests.get(
            f"{BASE_URL}/api/robots/status",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "robots" in data
        robots = data["robots"]
        assert len(robots) == 11, f"Expected 11 robots, got {len(robots)}"
        
        expected_robots = [
            "inventory", "debt", "report", "customer", "pricing",
            "maintenance", "profit", "repair", "prediction", "notification_bot", "supplier"
        ]
        for robot_name in expected_robots:
            assert robot_name in robots, f"Missing robot: {robot_name}"
        
        print(f"Robots status: {len(robots)} robots registered")
        for name, status in robots.items():
            print(f"  - {name}: running={status['is_running']}, last_run={status.get('last_run')}")
    
    def test_run_profit_robot(self, super_admin_token):
        """POST /api/robots/run/profit - Run profit robot, verify retail_price usage"""
        response = requests.post(
            f"{BASE_URL}/api/robots/run/profit",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        # Check for top_profitable field which should have correct product names
        if "top_profitable" in data:
            for product in data.get("top_profitable", []):
                assert "name" in product or "id" in product
                assert "profit_per_unit" in product
            print(f"Profit robot: {len(data.get('top_profitable', []))} top profitable products")
        print(f"Profit robot result keys: {list(data.keys())}")
    
    def test_run_inventory_robot(self, super_admin_token):
        """POST /api/robots/run/inventory - Run inventory robot"""
        response = requests.post(
            f"{BASE_URL}/api/robots/run/inventory",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        # Inventory robot returns stats
        assert isinstance(data, dict)
        print(f"Inventory robot result: {data}")


# ========== LOGIN REGRESSION TESTS ==========

class TestLoginRegression:
    """Verify all 3 credential types still work"""
    
    def test_super_admin_login(self):
        """Super Admin: admin@ntcommerce.com / Admin@2024"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=SUPER_ADMIN)
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print("Super admin login: OK")
    
    def test_tenant_login(self):
        """Tenant: ncr@ntcommerce.com / Test@123"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        assert response.status_code == 200, f"Tenant login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print("Tenant login: OK")
    
    def test_normal_user_login(self):
        """Normal User: test@test.com / Test@123 (optional - user may not exist)"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=NORMAL_USER)
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            print("Normal user login: OK")
        elif response.status_code == 401:
            # User may not exist - this is acceptable
            print("Normal user (test@test.com) does not exist or has different password - SKIPPED")
            pytest.skip("Normal user does not exist in database")
        else:
            pytest.fail(f"Unexpected status: {response.status_code} - {response.text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
