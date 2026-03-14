"""
Test Suite for Iteration 69 - Post-Cleanup Regression Testing
After removing ~3,735 lines of duplicate code from server.py (12,099 -> 8,364 lines).
Tests ALL 10 extracted route modules to verify NO REGRESSIONS:
- Products, Customers, Sales, Purchases, Stats, Employees, CashBox, Debts, Expenses, Daily Sessions (NEW)

All endpoints from the review request are tested here.
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TENANT_CREDS = {"email": "ncr@ntcommerce.com", "password": "Test@123"}
ADMIN_CREDS = {"email": "admin@ntcommerce.com", "password": "Admin@2024"}


@pytest.fixture(scope="module")
def tenant_token():
    """Get tenant authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_CREDS, timeout=30)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Tenant authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token for super admin operations"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=ADMIN_CREDS, timeout=30)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Admin authentication failed: {response.status_code}")


@pytest.fixture
def tenant_headers(tenant_token):
    """Headers with tenant authentication"""
    return {"Authorization": f"Bearer {tenant_token}", "Content-Type": "application/json"}


@pytest.fixture
def admin_headers(admin_token):
    """Headers with admin authentication"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ============ AUTH TESTS ============
class TestAuth:
    """Test authentication endpoints - CRITICAL"""
    
    def test_admin_login(self):
        """POST /api/auth/unified-login - admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=ADMIN_CREDS, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "Response should contain token"
        assert data.get("user_type") == "admin", f"User type should be 'admin', got {data.get('user_type')}"
        print(f"PASS: Admin login successful - user_type: {data.get('user_type')}")
    
    def test_tenant_login(self):
        """POST /api/auth/unified-login - tenant login works"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_CREDS, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "Response should contain token"
        assert data.get("user_type") == "tenant", f"User type should be 'tenant', got {data.get('user_type')}"
        print(f"PASS: Tenant login successful - user_type: {data.get('user_type')}")


# ============ PRODUCTS ROUTES (EXTRACTED) ============
class TestProductsRoutes:
    """Test Products routes (extracted to products_routes.py)"""

    def test_get_products_list(self, tenant_headers):
        """GET /api/products - List all products"""
        response = requests.get(f"{BASE_URL}/api/products", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Products list should be an array"
        print(f"PASS: GET /api/products returned {len(data)} products")

    def test_get_products_paginated(self, tenant_headers):
        """GET /api/products/paginated - Paginated products"""
        response = requests.get(f"{BASE_URL}/api/products/paginated?page=1&page_size=5", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        print(f"PASS: Paginated products - total: {data['total']}, items: {len(data['items'])}")

    def test_create_product(self, tenant_headers):
        """POST /api/products - Create product"""
        unique_id = str(uuid.uuid4())[:8]
        product_data = {
            "name_en": f"TEST_Product_{unique_id}",
            "name_ar": f"منتج_اختبار_{unique_id}",
            "purchase_price": 100,
            "wholesale_price": 150,
            "retail_price": 200,
            "quantity": 10
        }
        response = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=tenant_headers, timeout=30)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Created product should have 'id'"
        print(f"PASS: Created product with ID: {data['id']}")


# ============ CUSTOMERS ROUTES (EXTRACTED) ============
class TestCustomersRoutes:
    """Test Customers routes (extracted to customers_routes.py)"""

    def test_get_customers_list(self, tenant_headers):
        """GET /api/customers - List all customers"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Customers list should be an array"
        print(f"PASS: GET /api/customers returned {len(data)} customers")

    def test_create_customer(self, tenant_headers):
        """POST /api/customers - Create customer"""
        unique_id = str(uuid.uuid4())[:8]
        customer_data = {
            "name": f"تجربة_{unique_id}",
            "phone": f"0555{unique_id[:6]}"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=tenant_headers, timeout=30)
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Created customer should have 'id'"
        print(f"PASS: Created customer with ID: {data['id']}, name: {data.get('name')}")


# ============ SALES ROUTES (EXTRACTED) ============
class TestSalesRoutes:
    """Test Sales routes (extracted to sales_routes.py)"""

    def test_get_sales_list(self, tenant_headers):
        """GET /api/sales - List all sales"""
        response = requests.get(f"{BASE_URL}/api/sales", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Sales list should be an array"
        print(f"PASS: GET /api/sales returned {len(data)} sales")


# ============ PURCHASES ROUTES (EXTRACTED) ============
class TestPurchasesRoutes:
    """Test Purchases routes (extracted to purchases_routes.py)"""

    def test_get_purchases_list(self, tenant_headers):
        """GET /api/purchases - List all purchases"""
        response = requests.get(f"{BASE_URL}/api/purchases", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Purchases list should be an array"
        print(f"PASS: GET /api/purchases returned {len(data)} purchases")


# ============ CASHBOX ROUTES (EXTRACTED) ============
class TestCashboxRoutes:
    """Test Cash Box routes (extracted to cashbox_routes.py)"""

    def test_get_cash_boxes(self, tenant_headers):
        """GET /api/cash-boxes - Cash boxes"""
        response = requests.get(f"{BASE_URL}/api/cash-boxes", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Cash boxes should be an array"
        print(f"PASS: GET /api/cash-boxes returned {len(data)} boxes")

    def test_get_transactions(self, tenant_headers):
        """GET /api/transactions - Transactions"""
        response = requests.get(f"{BASE_URL}/api/transactions", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Transactions should be an array"
        print(f"PASS: GET /api/transactions returned {len(data)} transactions")


# ============ DEBTS ROUTES (EXTRACTED) ============
class TestDebtsRoutes:
    """Test Debts routes (extracted to debts_routes.py)"""

    def test_get_debts_list(self, tenant_headers):
        """GET /api/debts - Debts list"""
        response = requests.get(f"{BASE_URL}/api/debts", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Debts list should be an array"
        print(f"PASS: GET /api/debts returned {len(data)} debts")


# ============ EXPENSES ROUTES (EXTRACTED) ============
class TestExpensesRoutes:
    """Test Expenses routes (extracted to expenses_routes.py)"""

    def test_get_expenses_list(self, tenant_headers):
        """GET /api/expenses - Expenses list"""
        response = requests.get(f"{BASE_URL}/api/expenses", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expenses list should be an array"
        print(f"PASS: GET /api/expenses returned {len(data)} expenses")

    def test_get_expenses_stats(self, tenant_headers):
        """GET /api/expenses/stats - Expense stats"""
        response = requests.get(f"{BASE_URL}/api/expenses/stats", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total" in data, "Response should contain 'total'"
        print(f"PASS: Expenses stats - Total: {data['total']}")


# ============ EMPLOYEES ROUTES (EXTRACTED) ============
class TestEmployeesRoutes:
    """Test Employees routes (extracted to employees_routes.py)"""

    def test_get_employees_list(self, tenant_headers):
        """GET /api/employees - List all employees"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Employees list should be an array"
        print(f"PASS: GET /api/employees returned {len(data)} employees")

    def test_get_salary_report(self, tenant_headers):
        """GET /api/employees/salary-report - Salary report"""
        response = requests.get(f"{BASE_URL}/api/employees/salary-report", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Salary report should be an array"
        print(f"PASS: Salary report returned {len(data)} entries")


# ============ STATS/DASHBOARD ROUTES (EXTRACTED) ============
class TestStatsRoutes:
    """Test Stats/Dashboard routes (extracted to stats_routes.py)"""

    def test_get_stats(self, tenant_headers):
        """GET /api/stats - Dashboard stats"""
        response = requests.get(f"{BASE_URL}/api/stats", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total_products" in data, "Response should contain 'total_products'"
        print(f"PASS: Stats - Products: {data.get('total_products')}, Customers: {data.get('total_customers')}")

    def test_get_sales_stats(self, tenant_headers):
        """GET /api/dashboard/sales-stats - Sales period stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/sales-stats", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "today" in data, "Response should contain 'today'"
        print(f"PASS: Sales stats - Today: {data.get('today')}, Month: {data.get('month')}")

    def test_get_profit_stats(self, tenant_headers):
        """GET /api/dashboard/profit-stats - Profit stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/profit-stats", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "monthly_revenue" in data, "Response should contain 'monthly_revenue'"
        print(f"PASS: Profit stats - Revenue: {data.get('monthly_revenue')}, Profit: {data.get('monthly_profit')}")

    def test_sales_chart(self, tenant_headers):
        """GET /api/analytics/sales-chart?period=week - Chart data"""
        response = requests.get(f"{BASE_URL}/api/analytics/sales-chart?period=week", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "period" in data, "Response should contain 'period'"
        print(f"PASS: Sales chart - Period: {data.get('period')}, Data points: {len(data.get('data', []))}")

    def test_sales_prediction(self, tenant_headers):
        """GET /api/analytics/sales-prediction - AI prediction"""
        response = requests.get(f"{BASE_URL}/api/analytics/sales-prediction", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "trend" in data, "Response should contain 'trend'"
        print(f"PASS: Sales prediction - Trend: {data.get('trend')}")


# ============ DAILY SESSIONS ROUTES (NEW EXTRACTED) ============
class TestDailySessionsRoutes:
    """Test Daily Sessions routes (NEW extracted to daily_sessions_routes.py)"""

    def test_get_daily_sessions(self, tenant_headers):
        """GET /api/daily-sessions - List sessions"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Daily sessions should be an array"
        print(f"PASS: GET /api/daily-sessions returned {len(data)} sessions")

    def test_get_current_session(self, tenant_headers):
        """GET /api/daily-sessions/current - Current session"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions/current", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        # May be null if no open session
        print(f"PASS: GET /api/daily-sessions/current returned successfully")

    def test_create_daily_session(self, tenant_headers):
        """POST /api/daily-sessions - Create session"""
        # First check if there's an open session - close it or skip
        current = requests.get(f"{BASE_URL}/api/daily-sessions/current", headers=tenant_headers, timeout=30)
        if current.status_code == 200 and current.json():
            print("SKIP: Open session already exists, cannot create new one")
            pytest.skip("Open session exists")
        
        session_data = {
            "opening_cash": 5000,
            "opened_at": datetime.now().isoformat()
        }
        response = requests.post(f"{BASE_URL}/api/daily-sessions", json=session_data, headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Created session should have 'id'"
        print(f"PASS: Created daily session with ID: {data['id']}")
        
        # Clean up - close the session
        session_id = data["id"]
        close_data = {
            "closing_cash": 5000,
            "closed_at": datetime.now().isoformat(),
            "notes": "Test session closed"
        }
        requests.put(f"{BASE_URL}/api/daily-sessions/{session_id}/close", json=close_data, headers=tenant_headers, timeout=30)


# ============ REPAIR ROUTES ============
class TestRepairRoutes:
    """Test Repair routes"""

    def test_get_repair_tickets(self, tenant_headers):
        """GET /api/repairs/tickets - Repair tickets"""
        response = requests.get(f"{BASE_URL}/api/repairs/tickets", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Repair tickets should be an array"
        print(f"PASS: GET /api/repairs/tickets returned {len(data)} tickets")


# ============ DEFECTIVE ROUTES ============
class TestDefectiveRoutes:
    """Test Defective routes"""

    def test_get_defective_stats(self, tenant_headers):
        """GET /api/defective/stats - Defective stats"""
        response = requests.get(f"{BASE_URL}/api/defective/stats", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: GET /api/defective/stats returned successfully")


# ============ BACKUP ROUTES ============
class TestBackupRoutes:
    """Test Backup routes"""

    def test_get_backup_stats_summary(self, tenant_headers):
        """GET /api/backup/stats/summary - Backup summary"""
        response = requests.get(f"{BASE_URL}/api/backup/stats/summary", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: GET /api/backup/stats/summary returned successfully")


# ============ WALLET ROUTES ============
class TestWalletRoutes:
    """Test Wallet routes"""

    def test_get_wallet(self, tenant_headers):
        """GET /api/wallet - Wallet"""
        response = requests.get(f"{BASE_URL}/api/wallet", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"PASS: GET /api/wallet returned successfully")


# ============ PERMISSIONS ROUTES ============
class TestPermissionsRoutes:
    """Test Permissions routes"""

    def test_get_permissions_catalog(self, tenant_headers):
        """GET /api/permissions/catalog - Permissions catalog"""
        response = requests.get(f"{BASE_URL}/api/permissions/catalog", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, dict) or isinstance(data, list), "Permissions catalog should be dict or list"
        print(f"PASS: GET /api/permissions/catalog returned successfully")


# ============ SMART NOTIFICATIONS ROUTES ============
class TestSmartNotificationsRoutes:
    """Test Smart Notifications routes"""

    def test_get_smart_notifications(self, tenant_headers):
        """GET /api/smart-notifications - Smart notifications"""
        response = requests.get(f"{BASE_URL}/api/smart-notifications", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Smart notifications should be an array"
        print(f"PASS: GET /api/smart-notifications returned {len(data)} notifications")

    def test_get_legacy_notifications(self, tenant_headers):
        """GET /api/notifications - Legacy notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Notifications should be an array"
        print(f"PASS: GET /api/notifications returned {len(data)} notifications")


# ============ WAREHOUSE/SUPPLIER ROUTES ============
class TestWarehouseSupplierRoutes:
    """Test Warehouse and Supplier routes"""

    def test_get_warehouses(self, tenant_headers):
        """GET /api/warehouses - Warehouses"""
        response = requests.get(f"{BASE_URL}/api/warehouses", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Warehouses should be an array"
        print(f"PASS: GET /api/warehouses returned {len(data)} warehouses")

    def test_get_suppliers(self, tenant_headers):
        """GET /api/suppliers - Suppliers"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Suppliers should be an array"
        print(f"PASS: GET /api/suppliers returned {len(data)} suppliers")

    def test_get_product_families(self, tenant_headers):
        """GET /api/product-families - Product families"""
        response = requests.get(f"{BASE_URL}/api/product-families", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Product families should be an array"
        print(f"PASS: GET /api/product-families returned {len(data)} families")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
