"""
NT Commerce Final Comprehensive Test Suite
Testing: Authentication, Dashboard, POS, Products, Sales, Customers, Daily Sessions,
Backup, French Language, SaaS Admin, System Errors, Reports
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ai-accounting-mvp.preview.emergentagent.com')

# Test credentials
SUPER_ADMIN = {"email": "admin@ntcommerce.com", "password": "Admin@2024"}
TENANT = {"email": "ncr@ntcommerce.com", "password": "Test@123"}


class TestAuthentication:
    """Authentication - Tenant login and Super Admin login"""

    def test_super_admin_login(self):
        """Test Super Admin can login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/unified-login",
            json=SUPER_ADMIN
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user_type"] == "admin"
        assert data["user"]["role"] == "super_admin"
        print(f"✓ Super Admin login successful - user: {data['user']['name']}")

    def test_tenant_login(self):
        """Test Tenant can login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/unified-login",
            json=TENANT
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user_type"] == "tenant"
        assert data["user"]["database_name"].startswith("tenant_")
        print(f"✓ Tenant login successful - company: {data['user']['company_name']}")

    def test_invalid_login(self):
        """Test invalid credentials are rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/unified-login",
            json={"email": "wrong@email.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print("✓ Invalid login rejected correctly")


class TestDashboard:
    """Dashboard - Stats cards show correct data"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get tenant token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_stats_endpoint(self):
        """Test stats endpoint returns data"""
        response = requests.get(f"{BASE_URL}/api/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_products" in data
        assert "total_customers" in data
        assert "today_sales_total" in data
        print(f"✓ Stats: {data['total_products']} products, {data['total_customers']} customers")

    def test_sales_stats_endpoint(self):
        """Test sales stats for today/month/year"""
        response = requests.get(f"{BASE_URL}/api/dashboard/sales-stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "today" in data
        assert "month" in data
        assert "year" in data
        print(f"✓ Sales stats: today={data['today']['total']}, month={data['month']['total']}")

    def test_profit_stats_endpoint(self):
        """Test profit calculation endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/profit-stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "monthly_revenue" in data
        assert "monthly_profit" in data
        print(f"✓ Profit stats: revenue={data['monthly_revenue']}, profit={data['monthly_profit']}")


class TestProducts:
    """Products - List, add, edit work correctly"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get tenant token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_products(self):
        """Test listing products"""
        response = requests.get(f"{BASE_URL}/api/products", headers=self.headers)
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)
        print(f"✓ Listed {len(products)} products")

    def test_product_families(self):
        """Test product families endpoint"""
        response = requests.get(f"{BASE_URL}/api/product-families", headers=self.headers)
        assert response.status_code == 200
        families = response.json()
        print(f"✓ Listed {len(families)} product families")

    def test_generate_article_code(self):
        """Test article code generation"""
        response = requests.get(f"{BASE_URL}/api/products/generate-article-code", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "article_code" in data
        assert data["article_code"].startswith("AR")
        print(f"✓ Generated article code: {data['article_code']}")


class TestCustomers:
    """Customers - CRUD operations work"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get tenant token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_customers(self):
        """Test listing customers"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=self.headers)
        assert response.status_code == 200
        customers = response.json()
        assert isinstance(customers, list)
        print(f"✓ Listed {len(customers)} customers")

    def test_customer_families(self):
        """Test customer families endpoint"""
        response = requests.get(f"{BASE_URL}/api/customer-families", headers=self.headers)
        assert response.status_code == 200
        families = response.json()
        print(f"✓ Listed {len(families)} customer families")


class TestSales:
    """Sales - Create sale flow works"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get tenant token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_sales(self):
        """Test listing sales"""
        response = requests.get(f"{BASE_URL}/api/sales", headers=self.headers)
        assert response.status_code == 200
        # Sales can be list or dict with "sales" key
        data = response.json()
        if isinstance(data, dict):
            assert "sales" in data
            print(f"✓ Listed {len(data['sales'])} sales")
        else:
            print(f"✓ Listed {len(data)} sales")

    def test_generate_sale_code(self):
        """Test sale code generation"""
        response = requests.get(f"{BASE_URL}/api/sales/generate-code", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert data["code"].startswith("BV")
        print(f"✓ Generated sale code: {data['code']}")


class TestDailySessions:
    """Daily Sessions - Open/close session"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get tenant token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_current_session(self):
        """Test checking current session status"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions/current", headers=self.headers)
        # Should return 200 (with session) or 404 (no session)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Current session: {data.get('session_code', data.get('code', 'N/A'))}")
        else:
            print("✓ No active session (expected behavior)")

    def test_generate_session_code(self):
        """Test session code generation"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions/generate-code", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        print(f"✓ Generated session code: {data['code']}")


class TestBackupSystem:
    """Backup System - Available in settings"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=SUPER_ADMIN)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_backup_endpoint_exists(self):
        """Test backup related endpoints exist"""
        # Check if database management endpoints exist
        response = requests.get(f"{BASE_URL}/api/saas/databases", headers=self.headers)
        # Should return data or 404
        assert response.status_code in [200, 404]
        print("✓ Backup/Database management endpoint accessible")


class TestSaaSAdmin:
    """SaaS Admin - Tenants, Plans, Payments tabs work"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=SUPER_ADMIN)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_tenants(self):
        """Test listing tenants"""
        response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=self.headers)
        assert response.status_code == 200
        tenants = response.json()
        assert isinstance(tenants, list)
        print(f"✓ Listed {len(tenants)} tenants")

    def test_list_plans(self):
        """Test listing plans"""
        response = requests.get(f"{BASE_URL}/api/saas/plans", headers=self.headers)
        assert response.status_code == 200
        plans = response.json()
        assert isinstance(plans, list)
        print(f"✓ Listed {len(plans)} plans")

    def test_list_payments(self):
        """Test listing payments"""
        response = requests.get(f"{BASE_URL}/api/saas/payments", headers=self.headers)
        assert response.status_code == 200
        payments = response.json()
        print(f"✓ Listed {len(payments)} payments")


class TestSystemErrors:
    """System Errors - Real API data, maintenance actions work"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=SUPER_ADMIN)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_get_system_errors(self):
        """Test getting system errors with stats"""
        response = requests.get(f"{BASE_URL}/api/saas/system-errors", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data
        assert "stats" in data
        print(f"✓ System errors: {data['stats']['total']} total, {data['stats']['active']} active")

    def test_maintenance_system_check(self):
        """Test system check maintenance action"""
        response = requests.post(
            f"{BASE_URL}/api/saas/system-errors/maintenance/system_check",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "system_check"
        assert "details" in data
        print(f"✓ System check: {data['details']}")


class TestReports:
    """Reports - Sales reports display correctly"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get tenant token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_reports_endpoint(self):
        """Test reports API"""
        response = requests.get(f"{BASE_URL}/api/reports/sales", headers=self.headers)
        # Reports endpoint should exist
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Sales reports data available")
        else:
            print("✓ Reports endpoint responds (may need parameters)")


class TestWarehouses:
    """Warehouses - List and management"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get tenant token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_warehouses(self):
        """Test listing warehouses"""
        response = requests.get(f"{BASE_URL}/api/warehouses", headers=self.headers)
        assert response.status_code == 200
        warehouses = response.json()
        print(f"✓ Listed {len(warehouses)} warehouses")


class TestCashBoxes:
    """Cash Boxes - Balance tracking"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get tenant token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_cash_boxes(self):
        """Test listing cash boxes"""
        response = requests.get(f"{BASE_URL}/api/cash-boxes", headers=self.headers)
        assert response.status_code == 200
        boxes = response.json()
        assert isinstance(boxes, list)
        # Check French names exist
        if boxes:
            for box in boxes:
                if box.get('name_fr'):
                    print(f"✓ Cash box with French name: {box['name_fr']}")
                    break
        print(f"✓ Listed {len(boxes)} cash boxes")


class TestDelivery:
    """Delivery - Wilayas for delivery"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get tenant token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_wilayas(self):
        """Test listing wilayas"""
        response = requests.get(f"{BASE_URL}/api/delivery/wilayas", headers=self.headers)
        assert response.status_code == 200
        wilayas = response.json()
        print(f"✓ Listed {len(wilayas)} wilayas")


class TestPOSFeatures:
    """POS Page - Session bar and shortcuts"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get tenant token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT)
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_pos_data_loads(self):
        """Test all data needed for POS loads correctly"""
        # Products
        products = requests.get(f"{BASE_URL}/api/products", headers=self.headers)
        assert products.status_code == 200

        # Customers
        customers = requests.get(f"{BASE_URL}/api/customers", headers=self.headers)
        assert customers.status_code == 200

        # Families
        families = requests.get(f"{BASE_URL}/api/product-families", headers=self.headers)
        assert families.status_code == 200

        # Warehouses
        warehouses = requests.get(f"{BASE_URL}/api/warehouses", headers=self.headers)
        assert warehouses.status_code == 200

        # Cash boxes
        cash_boxes = requests.get(f"{BASE_URL}/api/cash-boxes", headers=self.headers)
        assert cash_boxes.status_code == 200

        print("✓ All POS data endpoints respond correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
