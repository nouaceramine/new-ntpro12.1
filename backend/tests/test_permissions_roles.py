"""
Test suite for Advanced Roles and Permissions System
Tests the new role system with 9 roles including:
- super_admin, admin, manager, sales_supervisor, seller
- inventory_manager, ecommerce_manager, accountant, user

Also tests permission categories and role-specific permissions.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDENTIALS = {
    "email": "admin@test.com",
    "password": "admin123"
}


class TestPermissionsRolesAPI:
    """Tests for /api/permissions/roles endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_auth_token(self):
        """Get authentication token"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=ADMIN_CREDENTIALS
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_get_roles_returns_9_roles(self):
        """API: GET /api/permissions/roles should return 9 roles"""
        response = self.session.get(f"{BASE_URL}/api/permissions/roles")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "roles" in data, "Response should contain 'roles' key"
        
        expected_roles = [
            "super_admin", "admin", "manager", "sales_supervisor", "seller",
            "inventory_manager", "ecommerce_manager", "accountant", "user"
        ]
        
        roles = data["roles"]
        assert len(roles) == 9, f"Expected 9 roles, got {len(roles)}: {roles}"
        
        for role in expected_roles:
            assert role in roles, f"Role '{role}' should be in roles list"
            
        print(f"PASS: GET /api/permissions/roles returns 9 roles: {roles}")
    
    def test_get_roles_includes_default_permissions(self):
        """API: GET /api/permissions/roles should include default_permissions"""
        response = self.session.get(f"{BASE_URL}/api/permissions/roles")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "default_permissions" in data, "Response should contain 'default_permissions' key"
        
        default_permissions = data["default_permissions"]
        assert isinstance(default_permissions, dict), "default_permissions should be a dict"
        
        # Verify each role has permissions
        for role in data["roles"]:
            assert role in default_permissions, f"Role '{role}' should have default permissions"
            
        print(f"PASS: default_permissions contains all {len(default_permissions)} roles")
    
    def test_get_roles_includes_role_descriptions(self):
        """API: GET /api/permissions/roles should include role_descriptions"""
        response = self.session.get(f"{BASE_URL}/api/permissions/roles")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "role_descriptions" in data, "Response should contain 'role_descriptions' key"
        
        descriptions = data["role_descriptions"]
        
        # Check for Arabic and French descriptions
        for role in data["roles"]:
            assert role in descriptions, f"Role '{role}' should have a description"
            assert "ar" in descriptions[role], f"Role '{role}' should have Arabic description"
            assert "fr" in descriptions[role], f"Role '{role}' should have French description"
            
        print(f"PASS: All roles have Arabic and French descriptions")
    
    def test_get_roles_includes_permission_categories(self):
        """API: GET /api/permissions/roles should include permission_categories"""
        response = self.session.get(f"{BASE_URL}/api/permissions/roles")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "permission_categories" in data, "Response should contain 'permission_categories' key"
        
        categories = data["permission_categories"]
        assert isinstance(categories, dict), "permission_categories should be a dict"
        
        print(f"PASS: permission_categories returned with {len(categories)} categories")


class TestPermissionCategories:
    """Tests for /api/permissions/categories endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_get_permission_categories(self):
        """API: GET /api/permissions/categories should return category definitions"""
        response = self.session.get(f"{BASE_URL}/api/permissions/categories")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        categories = response.json()
        
        # Expected categories based on backend code
        expected_categories = [
            "sales_operations",
            "inventory_operations", 
            "hr_operations",
            "financial",
            "system",
            "services"
        ]
        
        for cat in expected_categories:
            assert cat in categories, f"Category '{cat}' should exist"
            assert "ar" in categories[cat], f"Category '{cat}' should have Arabic name"
            assert "fr" in categories[cat], f"Category '{cat}' should have French name"
            assert "permissions" in categories[cat], f"Category '{cat}' should have permissions list"
            
        print(f"PASS: GET /api/permissions/categories returns {len(categories)} categories")
    
    def test_sales_operations_category(self):
        """Verify sales_operations category contains: pos, sales, customers, debts"""
        response = self.session.get(f"{BASE_URL}/api/permissions/categories")
        
        assert response.status_code == 200
        categories = response.json()
        
        sales_ops = categories.get("sales_operations", {})
        assert sales_ops.get("ar") == "عمليات المبيعات"
        
        expected_perms = ["pos", "sales", "customers", "debts"]
        actual_perms = sales_ops.get("permissions", [])
        
        for perm in expected_perms:
            assert perm in actual_perms, f"sales_operations should include '{perm}'"
            
        print(f"PASS: sales_operations category correct: {actual_perms}")
    
    def test_inventory_operations_category(self):
        """Verify inventory_operations category contains: products, inventory, purchases, suppliers"""
        response = self.session.get(f"{BASE_URL}/api/permissions/categories")
        
        assert response.status_code == 200
        categories = response.json()
        
        inv_ops = categories.get("inventory_operations", {})
        expected_perms = ["products", "inventory", "purchases", "suppliers"]
        actual_perms = inv_ops.get("permissions", [])
        
        for perm in expected_perms:
            assert perm in actual_perms, f"inventory_operations should include '{perm}'"
            
        print(f"PASS: inventory_operations category correct: {actual_perms}")


class TestRoleSpecificPermissions:
    """Tests for /api/permissions/role/{role_name} endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_get_sales_supervisor_permissions(self):
        """API: GET /api/permissions/role/sales_supervisor should return correct permissions"""
        response = self.session.get(f"{BASE_URL}/api/permissions/role/sales_supervisor")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["role"] == "sales_supervisor"
        
        # Verify description exists
        assert "description" in data
        assert "ar" in data["description"]
        assert "مبيعات" in data["description"]["ar"]  # Should mention sales
        
        # Verify permissions
        perms = data["permissions"]
        
        # Sales supervisor should see sales reports only, NOT financial
        reports = perms.get("reports", {})
        assert reports.get("sales") == True, "sales_supervisor should have sales reports"
        assert reports.get("financial") == False, "sales_supervisor should NOT have financial reports"
        assert reports.get("inventory") == False, "sales_supervisor should NOT have inventory reports"
        
        # Should have sales permissions with refund and discount
        sales = perms.get("sales", {})
        assert sales.get("view") == True
        assert sales.get("refund") == True
        assert sales.get("discount") == True
        
        print(f"PASS: sales_supervisor has correct permissions")
    
    def test_get_inventory_manager_permissions(self):
        """API: GET /api/permissions/role/inventory_manager should return correct permissions"""
        response = self.session.get(f"{BASE_URL}/api/permissions/role/inventory_manager")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["role"] == "inventory_manager"
        
        perms = data["permissions"]
        
        # Inventory manager should see inventory reports only, NOT financial
        reports = perms.get("reports", {})
        assert reports.get("inventory") == True, "inventory_manager should have inventory reports"
        assert reports.get("financial") == False, "inventory_manager should NOT have financial reports"
        assert reports.get("sales") == False, "inventory_manager should NOT have sales reports"
        
        # Should have full inventory permissions
        inventory = perms.get("inventory", {})
        assert inventory.get("view") == True
        assert inventory.get("transfer") == True
        assert inventory.get("count") == True
        
        # Should have stock_adjust permission on products
        products = perms.get("products", {})
        assert products.get("stock_adjust") == True
        
        print(f"PASS: inventory_manager has correct permissions")
    
    def test_get_accountant_permissions(self):
        """API: GET /api/permissions/role/accountant should return correct permissions"""
        response = self.session.get(f"{BASE_URL}/api/permissions/role/accountant")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["role"] == "accountant"
        
        perms = data["permissions"]
        
        # Accountant should see financial reports
        reports = perms.get("reports", {})
        assert reports.get("financial") == True, "accountant should have financial reports"
        assert reports.get("sales") == True, "accountant should have sales reports"
        assert reports.get("advanced") == True, "accountant should have advanced reports"
        
        # Should have expenses permissions
        expenses = perms.get("expenses", {})
        assert expenses.get("view") == True
        assert expenses.get("approve") == True
        
        # Should NOT have POS access
        assert perms.get("pos") == False, "accountant should NOT have POS access"
        
        print(f"PASS: accountant has correct permissions")
    
    def test_get_invalid_role(self):
        """API: GET /api/permissions/role/invalid_role should return 404"""
        response = self.session.get(f"{BASE_URL}/api/permissions/role/invalid_role_xyz")
        
        assert response.status_code == 404, f"Expected 404 for invalid role, got {response.status_code}"
        
        print(f"PASS: Invalid role returns 404")


class TestAdvancedPermissionActions:
    """Tests for advanced permission actions like price_change, refund, discount, etc."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_super_admin_has_all_advanced_permissions(self):
        """Verify super_admin has all advanced permissions"""
        response = self.session.get(f"{BASE_URL}/api/permissions/role/super_admin")
        
        assert response.status_code == 200
        perms = response.json()["permissions"]
        
        # Check products advanced permissions
        products = perms.get("products", {})
        assert products.get("price_change") == True
        assert products.get("stock_adjust") == True
        
        # Check sales advanced permissions
        sales = perms.get("sales", {})
        assert sales.get("refund") == True
        assert sales.get("discount") == True
        
        # Check customers advanced permissions
        customers = perms.get("customers", {})
        assert customers.get("credit") == True
        assert customers.get("blacklist") == True
        
        # Check inventory advanced permissions
        inventory = perms.get("inventory", {})
        assert inventory.get("transfer") == True
        assert inventory.get("count") == True
        
        # Check saas_admin permission
        assert perms.get("saas_admin") == True
        
        print(f"PASS: super_admin has all advanced permissions")
    
    def test_seller_limited_permissions(self):
        """Verify seller has limited permissions"""
        response = self.session.get(f"{BASE_URL}/api/permissions/role/seller")
        
        assert response.status_code == 200
        perms = response.json()["permissions"]
        
        # Seller should NOT have advanced permissions
        products = perms.get("products", {})
        assert products.get("price_change") == False
        assert products.get("add") == False
        assert products.get("edit") == False
        
        sales = perms.get("sales", {})
        assert sales.get("refund") == False
        assert sales.get("discount") == False
        
        # But should have basic sales
        assert perms.get("pos") == True
        assert sales.get("view") == True
        assert sales.get("add") == True
        
        print(f"PASS: seller has correctly limited permissions")


class TestUserPermissionsAPI:
    """Tests for user-specific permissions endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
    
    def get_auth_token(self):
        """Get authentication token"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=ADMIN_CREDENTIALS
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return self.token
        return None
    
    def test_login_and_get_current_user(self):
        """Verify admin login works"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=ADMIN_CREDENTIALS
        )
        
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
        
        print(f"PASS: Admin login successful, role: {data['user']['role']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
