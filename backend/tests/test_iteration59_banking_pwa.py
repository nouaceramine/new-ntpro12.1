"""
Iteration 59 Tests: Banking Integration, Notification Bell, PWA
Tests for new features: bank accounts, transactions, reconciliation, notifications, manifest.json
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TENANT_EMAIL = "ncr@ntcommerce.com"
TENANT_PASSWORD = "Test@123"
SUPER_ADMIN_EMAIL = "admin@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "Admin@2024"


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_tenant_login(self):
        """Test tenant user can login"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0
    
    def test_super_admin_login(self):
        """Test super admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


class TestPWA:
    """Test PWA manifest and service worker"""
    
    def test_manifest_json_accessible(self):
        """PWA manifest.json should be accessible"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NT Commerce - منصة محاسبة ذكية"
        assert data["short_name"] == "NT Commerce"
        assert data["display"] == "standalone"
        assert "icons" in data
        assert len(data["icons"]) >= 2
    
    def test_service_worker_accessible(self):
        """Service worker should be accessible"""
        response = requests.get(f"{BASE_URL}/service-worker.js")
        assert response.status_code == 200
        assert "CACHE_NAME" in response.text or "self.addEventListener" in response.text


class TestNotifications:
    """Test notification endpoints"""
    
    @pytest.fixture
    def tenant_token(self):
        """Get tenant auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_notifications_unread_count(self, tenant_token):
        """GET /api/notifications/unread-count should return count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)
    
    def test_notifications_list(self, tenant_token):
        """GET /api/notifications/ should return notifications list"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/?limit=20",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestBankingAccounts:
    """Test banking account CRUD operations"""
    
    @pytest.fixture
    def tenant_token(self):
        """Get tenant auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_get_banking_summary(self, tenant_token):
        """GET /api/banking/summary should return summary"""
        response = requests.get(
            f"{BASE_URL}/api/banking/summary",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_accounts" in data
        assert "active_accounts" in data
        assert "total_balance" in data
        assert "accounts" in data
        assert "transaction_summary" in data
    
    def test_get_bank_accounts(self, tenant_token):
        """GET /api/banking/accounts should return accounts list"""
        response = requests.get(
            f"{BASE_URL}/api/banking/accounts",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_bank_account(self, tenant_token):
        """POST /api/banking/accounts should create a bank account"""
        account_data = {
            "bank_name": f"TEST_Bank_{uuid.uuid4().hex[:6]}",
            "bank_name_ar": "بنك اختباري",
            "account_number": f"TEST{uuid.uuid4().hex[:8]}",
            "iban": "DZ9999999999999999999",
            "swift_code": "TESTALG",
            "account_type": "current",
            "currency": "DZD",
            "initial_balance": 10000,
            "is_primary": False
        }
        response = requests.post(
            f"{BASE_URL}/api/banking/accounts",
            json=account_data,
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["bank_name"] == account_data["bank_name"]
        assert data["current_balance"] == account_data["initial_balance"]
        assert data["is_active"] == True
        
        # Cleanup - delete the test account
        account_id = data["id"]
        requests.delete(
            f"{BASE_URL}/api/banking/accounts/{account_id}",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )


class TestBankingTransactions:
    """Test banking transaction operations"""
    
    @pytest.fixture
    def tenant_token(self):
        """Get tenant auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        return response.json().get("access_token")
    
    @pytest.fixture
    def test_account(self, tenant_token):
        """Create a test bank account for transaction tests"""
        account_data = {
            "bank_name": f"TEST_TX_Bank_{uuid.uuid4().hex[:6]}",
            "bank_name_ar": "بنك عمليات",
            "account_number": f"TX{uuid.uuid4().hex[:8]}",
            "account_type": "current",
            "currency": "DZD",
            "initial_balance": 100000,
            "is_primary": False
        }
        response = requests.post(
            f"{BASE_URL}/api/banking/accounts",
            json=account_data,
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        account = response.json()
        yield account
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/banking/accounts/{account['id']}",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
    
    def test_get_transactions(self, tenant_token):
        """GET /api/banking/transactions should return transactions list"""
        response = requests.get(
            f"{BASE_URL}/api/banking/transactions",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_deposit_transaction(self, tenant_token, test_account):
        """POST /api/banking/transactions should create a deposit"""
        tx_data = {
            "bank_account_id": test_account["id"],
            "type": "deposit",
            "amount": 5000,
            "description": "Test deposit",
            "reference": "TEST-DEP"
        }
        response = requests.post(
            f"{BASE_URL}/api/banking/transactions",
            json=tx_data,
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "deposit"
        assert data["amount"] == 5000
        assert data["balance_after"] == 105000  # 100000 + 5000
    
    def test_create_withdrawal_transaction(self, tenant_token, test_account):
        """POST /api/banking/transactions should create a withdrawal"""
        tx_data = {
            "bank_account_id": test_account["id"],
            "type": "withdrawal",
            "amount": 2000,
            "description": "Test withdrawal",
            "reference": "TEST-WDR"
        }
        response = requests.post(
            f"{BASE_URL}/api/banking/transactions",
            json=tx_data,
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "withdrawal"
        assert data["amount"] == 2000
    
    def test_transaction_with_invalid_account(self, tenant_token):
        """POST /api/banking/transactions with invalid account should return 404"""
        tx_data = {
            "bank_account_id": "invalid-account-id",
            "type": "deposit",
            "amount": 1000,
            "description": "Test invalid"
        }
        response = requests.post(
            f"{BASE_URL}/api/banking/transactions",
            json=tx_data,
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 404


class TestBankingReconciliation:
    """Test banking reconciliation operations"""
    
    @pytest.fixture
    def tenant_token(self):
        """Get tenant auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        return response.json().get("access_token")
    
    @pytest.fixture
    def reconcile_account(self, tenant_token):
        """Create a test account for reconciliation"""
        account_data = {
            "bank_name": f"TEST_REC_Bank_{uuid.uuid4().hex[:6]}",
            "bank_name_ar": "بنك مطابقة",
            "account_number": f"REC{uuid.uuid4().hex[:8]}",
            "account_type": "current",
            "currency": "DZD",
            "initial_balance": 50000,
            "is_primary": False
        }
        response = requests.post(
            f"{BASE_URL}/api/banking/accounts",
            json=account_data,
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        account = response.json()
        yield account
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/banking/accounts/{account['id']}",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
    
    def test_reconcile_matching_balance(self, tenant_token, reconcile_account):
        """POST /api/banking/reconcile with matching balance should return matched status"""
        reconcile_data = {
            "bank_account_id": reconcile_account["id"],
            "statement_balance": 50000,  # Same as initial balance
            "statement_date": "2026-03-13"
        }
        response = requests.post(
            f"{BASE_URL}/api/banking/reconcile",
            json=reconcile_data,
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "matched"
        assert data["difference"] == 0
        assert data["system_balance"] == 50000
        assert data["statement_balance"] == 50000
    
    def test_reconcile_with_difference(self, tenant_token, reconcile_account):
        """POST /api/banking/reconcile with difference should return unmatched status"""
        reconcile_data = {
            "bank_account_id": reconcile_account["id"],
            "statement_balance": 55000,  # Different from initial balance
            "statement_date": "2026-03-13"
        }
        response = requests.post(
            f"{BASE_URL}/api/banking/reconcile",
            json=reconcile_data,
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unmatched"
        assert data["difference"] == 5000
    
    def test_get_reconciliations(self, tenant_token):
        """GET /api/banking/reconciliations should return reconciliation history"""
        response = requests.get(
            f"{BASE_URL}/api/banking/reconciliations",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestSaaSAdmin:
    """Test SaaS Admin endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get super admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_saas_stats_shows_active_tenant(self, admin_token):
        """GET /api/saas/stats should show 1 active tenant"""
        response = requests.get(
            f"{BASE_URL}/api/saas/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_tenants"] >= 1
        assert data["active_tenants"] >= 1


class TestExistingFeatures:
    """Verify existing features still work"""
    
    @pytest.fixture
    def tenant_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        return response.json().get("access_token")
    
    def test_tax_rates_endpoint(self, tenant_token):
        """GET /api/tax/rates should return tax rates"""
        response = requests.get(
            f"{BASE_URL}/api/tax/rates",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_currencies_endpoint(self, tenant_token):
        """GET /api/currencies/ should return currencies"""
        response = requests.get(
            f"{BASE_URL}/api/currencies/",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 10
    
    def test_whatsapp_config_endpoint(self, tenant_token):
        """GET /api/whatsapp/config should return config"""
        response = requests.get(
            f"{BASE_URL}/api/whatsapp/config",
            headers={"Authorization": f"Bearer {tenant_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "verify_token" in data or "phone_number_id" in data or isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
