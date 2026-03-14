"""
Test Suite for Iteration 68 - All Extracted Routes Testing
Tests ALL 9 extracted route modules from server.py:
- Previously extracted (iter 67): Products, Customers, Sales, Purchases, Stats
- Newly extracted (iter 68): Employees, CashBox, Debts, Expenses

Each module uses factory pattern: create_xxx_routes(db, get_current_user, ...)
"""
import pytest
import requests
import os
import uuid

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
    """Test authentication endpoints"""
    
    def test_admin_login(self):
        """POST /api/auth/unified-login - admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=ADMIN_CREDS, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "Response should contain token"
        print("PASS: Admin login successful")
    
    def test_tenant_login(self):
        """POST /api/auth/unified-login - tenant login works"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_CREDS, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "Response should contain token"
        print("PASS: Tenant login successful")


# ============ PRODUCTS ROUTES (EXTRACTED) ============
class TestProductsExtractedRoutes:
    """Test Products routes extracted from server.py to products_routes.py"""

    def test_get_products_list(self, tenant_headers):
        """GET /api/products - List all products (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/products", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Products list should be an array"
        print(f"PASS: GET /api/products returned {len(data)} products")

    def test_get_products_paginated(self, tenant_headers):
        """GET /api/products/paginated - Paginated products (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/products/paginated?page=1&page_size=5", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        print(f"PASS: Paginated products - total: {data['total']}, items: {len(data['items'])}")

    def test_generate_barcode(self, tenant_headers):
        """GET /api/products/generate-barcode - Generate barcode (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/products/generate-barcode", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "barcode" in data, "Response should contain 'barcode'"
        print(f"PASS: Generated barcode: {data['barcode']}")

    def test_low_stock_alerts(self, tenant_headers):
        """GET /api/products/alerts/low-stock - Low stock alerts (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/products/alerts/low-stock", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Low stock alerts should be an array"
        print(f"PASS: Low stock alerts returned {len(data)} products")


# ============ CUSTOMERS ROUTES (EXTRACTED) ============
class TestCustomersExtractedRoutes:
    """Test Customers routes extracted from server.py to customers_routes.py"""

    def test_get_customers_list(self, tenant_headers):
        """GET /api/customers - List all customers (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Customers list should be an array"
        print(f"PASS: GET /api/customers returned {len(data)} customers")

    def test_generate_customer_code(self, tenant_headers):
        """GET /api/customers/generate-code - Generate customer code (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/customers/generate-code", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "code" in data, "Response should contain 'code'"
        print(f"PASS: Generated customer code: {data['code']}")


# ============ SALES ROUTES (EXTRACTED) ============
class TestSalesExtractedRoutes:
    """Test Sales routes extracted from server.py to sales_routes.py"""

    def test_get_sales_list(self, tenant_headers):
        """GET /api/sales - List all sales (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/sales", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Sales list should be an array"
        print(f"PASS: GET /api/sales returned {len(data)} sales")

    def test_generate_sale_code(self, tenant_headers):
        """GET /api/sales/generate-code - Generate sale code (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/sales/generate-code", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "code" in data, "Response should contain 'code'"
        print(f"PASS: Generated sale code: {data['code']}")


# ============ PURCHASES ROUTES (EXTRACTED) ============
class TestPurchasesExtractedRoutes:
    """Test Purchases routes extracted from server.py to purchases_routes.py"""

    def test_get_purchases_list(self, tenant_headers):
        """GET /api/purchases - List all purchases (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/purchases", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Purchases list should be an array"
        print(f"PASS: GET /api/purchases returned {len(data)} purchases")

    def test_generate_purchase_code(self, tenant_headers):
        """GET /api/purchases/generate-code - Generate purchase code (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/purchases/generate-code", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "code" in data, "Response should contain 'code'"
        print(f"PASS: Generated purchase code: {data['code']}")


# ============ STATS ROUTES (EXTRACTED) ============
class TestStatsExtractedRoutes:
    """Test Stats/Dashboard routes extracted from server.py to stats_routes.py"""

    def test_get_stats(self, tenant_headers):
        """GET /api/stats - Dashboard stats (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/stats", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total_products" in data, "Response should contain 'total_products'"
        assert "total_customers" in data, "Response should contain 'total_customers'"
        print(f"PASS: Stats - Products: {data['total_products']}, Customers: {data['total_customers']}")

    def test_get_sales_stats(self, tenant_headers):
        """GET /api/dashboard/sales-stats - Sales period stats (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/sales-stats", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "today" in data, "Response should contain 'today'"
        assert "month" in data, "Response should contain 'month'"
        print(f"PASS: Sales stats - Today: {data['today']}, Month: {data['month']}")

    def test_get_profit_stats(self, tenant_headers):
        """GET /api/dashboard/profit-stats - Profit stats (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/profit-stats", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "monthly_revenue" in data, "Response should contain 'monthly_revenue'"
        assert "monthly_profit" in data, "Response should contain 'monthly_profit'"
        print(f"PASS: Profit stats - Revenue: {data['monthly_revenue']}, Profit: {data['monthly_profit']}")

    def test_sales_chart(self, tenant_headers):
        """GET /api/analytics/sales-chart?period=week - Chart data (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/analytics/sales-chart?period=week", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "period" in data, "Response should contain 'period'"
        assert "data" in data, "Response should contain 'data'"
        print(f"PASS: Sales chart - Period: {data['period']}, Data points: {len(data['data'])}")

    def test_sales_prediction(self, tenant_headers):
        """GET /api/analytics/sales-prediction - AI prediction (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/analytics/sales-prediction", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "trend" in data, "Response should contain 'trend'"
        print(f"PASS: Sales prediction - Trend: {data['trend']}")


# ============ EMPLOYEES ROUTES (NEW EXTRACTED) ============
class TestEmployeesExtractedRoutes:
    """Test Employees routes extracted from server.py to employees_routes.py - NEW in iter 68"""

    def test_get_employees_list(self, tenant_headers):
        """GET /api/employees - List all employees (NEW extracted route)"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Employees list should be an array"
        print(f"PASS: GET /api/employees returned {len(data)} employees")

    def test_get_salary_report(self, tenant_headers):
        """GET /api/employees/salary-report - Salary report (NEW extracted route)"""
        response = requests.get(f"{BASE_URL}/api/employees/salary-report", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Salary report should be an array"
        print(f"PASS: Salary report returned {len(data)} entries")

    def test_get_active_alerts(self, tenant_headers):
        """GET /api/employees/alerts/active - Employee alerts (NEW extracted route)"""
        response = requests.get(f"{BASE_URL}/api/employees/alerts/active", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Active alerts should be an array"
        print(f"PASS: Active alerts returned {len(data)} alerts")

    def test_create_employee(self, tenant_headers):
        """POST /api/employees - Create employee (NEW extracted route)"""
        unique_id = str(uuid.uuid4())[:8]
        employee_data = {
            "name": f"TEST_Employee_{unique_id}",
            "phone": f"0555{unique_id[:6]}",
            "salary": 50000,
            "commission_rate": 5
        }
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Created employee should have 'id'"
        assert data["name"] == employee_data["name"], "Name should match"
        print(f"PASS: Created employee with ID: {data['id']}, name: {data['name']}")
        return data["id"]


# ============ CASHBOX ROUTES (NEW EXTRACTED) ============
class TestCashboxExtractedRoutes:
    """Test Cash Box routes extracted from server.py to cashbox_routes.py - NEW in iter 68"""

    def test_get_cash_boxes(self, tenant_headers):
        """GET /api/cash-boxes - Cash boxes (NEW extracted route)"""
        response = requests.get(f"{BASE_URL}/api/cash-boxes", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Cash boxes should be an array"
        # Default boxes: cash, bank, wallet, safe
        assert len(data) >= 1, "Should have at least one cash box"
        print(f"PASS: GET /api/cash-boxes returned {len(data)} boxes")


# ============ TRANSACTIONS ROUTES (NEW EXTRACTED) ============
class TestTransactionsExtractedRoutes:
    """Test Transactions routes from cashbox_routes.py - NEW in iter 68"""

    def test_get_transactions(self, tenant_headers):
        """GET /api/transactions - Transactions (NEW extracted route)"""
        response = requests.get(f"{BASE_URL}/api/transactions", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Transactions should be an array"
        print(f"PASS: GET /api/transactions returned {len(data)} transactions")


# ============ DEBTS ROUTES (NEW EXTRACTED) ============
class TestDebtsExtractedRoutes:
    """Test Debts routes extracted from server.py to debts_routes.py - NEW in iter 68"""

    def test_get_debts_list(self, tenant_headers):
        """GET /api/debts - Debts list (NEW extracted route)"""
        response = requests.get(f"{BASE_URL}/api/debts", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Debts list should be an array"
        print(f"PASS: GET /api/debts returned {len(data)} debts")

    def test_create_debt(self, tenant_headers):
        """POST /api/debts - Create debt (NEW extracted route)"""
        # First get a customer to use as party
        customers_resp = requests.get(f"{BASE_URL}/api/customers", headers=tenant_headers, timeout=30)
        if customers_resp.status_code != 200 or not customers_resp.json():
            pytest.skip("No customers available for debt test")
        
        customers = customers_resp.json()
        if len(customers) == 0:
            pytest.skip("No customers available for debt test")
        
        customer = customers[0]
        
        debt_data = {
            "type": "receivable",
            "party_type": "customer",
            "party_id": customer["id"],
            "amount": 1000,
            "notes": "TEST debt for iteration 68"
        }
        response = requests.post(f"{BASE_URL}/api/debts", json=debt_data, headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Created debt should have 'id'"
        assert data["party_name"] == customer["name"], "Party name should match customer"
        print(f"PASS: Created debt with ID: {data['id']}, party: {data['party_name']}")


# ============ EXPENSES ROUTES (NEW EXTRACTED) ============
class TestExpensesExtractedRoutes:
    """Test Expenses routes extracted from server.py to expenses_routes.py - NEW in iter 68"""

    def test_get_expenses_list(self, tenant_headers):
        """GET /api/expenses - Expenses list (NEW extracted route)"""
        response = requests.get(f"{BASE_URL}/api/expenses", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expenses list should be an array"
        print(f"PASS: GET /api/expenses returned {len(data)} expenses")

    def test_get_expenses_stats(self, tenant_headers):
        """GET /api/expenses/stats - Expense stats (NEW extracted route)"""
        response = requests.get(f"{BASE_URL}/api/expenses/stats", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total" in data, "Response should contain 'total'"
        assert "thisMonth" in data, "Response should contain 'thisMonth'"
        print(f"PASS: Expenses stats - Total: {data['total']}, This Month: {data['thisMonth']}")

    def test_get_expense_reminders(self, tenant_headers):
        """GET /api/expenses/reminders - Recurring reminders (NEW extracted route)"""
        response = requests.get(f"{BASE_URL}/api/expenses/reminders", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Reminders should be an array"
        print(f"PASS: Expense reminders returned {len(data)} reminders")

    def test_create_expense(self, tenant_headers):
        """POST /api/expenses - Create expense (NEW extracted route)"""
        unique_id = str(uuid.uuid4())[:8]
        expense_data = {
            "title": f"TEST_Expense_{unique_id}",
            "category": "utilities",
            "amount": 500.0,
            "notes": "Test expense for iteration 68"
        }
        response = requests.post(f"{BASE_URL}/api/expenses", json=expense_data, headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Created expense should have 'id'"
        assert data["title"] == expense_data["title"], "Title should match"
        print(f"PASS: Created expense with ID: {data['id']}, title: {data['title']}")


# ============ REGRESSION TESTS ============
class TestRegressionAPIs:
    """Regression tests to ensure existing APIs still work"""

    def test_smart_notifications_api(self, tenant_headers):
        """GET /api/smart-notifications - Verify backend API still works"""
        response = requests.get(f"{BASE_URL}/api/smart-notifications", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Smart notifications API working")

    def test_permissions_catalog(self, tenant_headers):
        """GET /api/permissions/catalog - Permissions still working"""
        response = requests.get(f"{BASE_URL}/api/permissions/catalog", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Permissions catalog API working")

    def test_repairs_api(self, tenant_headers):
        """GET /api/repairs - Repairs still working"""
        response = requests.get(f"{BASE_URL}/api/repairs", headers=tenant_headers, timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Repairs API working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
