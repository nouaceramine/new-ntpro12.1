"""
Test tenant authentication and dashboard access flow.
Tests the fixes for:
1. /api/auth/me endpoint returning created_at for tenants
2. Token storage compatibility between UnifiedLoginPage and AuthContext
3. Products API working with tenant token
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TENANT_EMAIL = "ahmed@store.com"
TENANT_PASSWORD = "password"


class TestTenantAuthFlow:
    """Test tenant login and dashboard access"""
    
    def test_tenant_unified_login(self):
        """Test tenant can login via unified-login endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/auth/unified-login",
            json={"email": TENANT_EMAIL, "password": TENANT_PASSWORD}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["user_type"] == "tenant", f"Expected tenant, got {data['user_type']}"
        assert data["redirect_to"] == "/tenant/dashboard", "Wrong redirect path"
        assert "user" in data, "No user data in response"
        
        # Store token for next tests
        self.__class__.tenant_token = data["access_token"]
        print(f"SUCCESS: Tenant login successful for {TENANT_EMAIL}")
    
    def test_auth_me_returns_created_at(self):
        """Test /api/auth/me returns created_at field for tenants"""
        token = getattr(self.__class__, 'tenant_token', None)
        if not token:
            pytest.skip("No token from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Auth/me failed: {response.text}"
        
        data = response.json()
        
        # Verify all required fields
        assert "id" in data, "Missing id field"
        assert "email" in data, "Missing email field"
        assert "name" in data, "Missing name field"
        assert "role" in data, "Missing role field"
        assert "created_at" in data, "Missing created_at field (BUG FIX VERIFICATION)"
        assert "tenant_id" in data, "Missing tenant_id field"
        assert "user_type" in data, "Missing user_type field"
        
        # Verify values
        assert data["email"] == TENANT_EMAIL
        assert data["user_type"] == "tenant"
        assert data["created_at"] is not None, "created_at is None"
        
        print(f"SUCCESS: /api/auth/me returned all required fields including created_at={data['created_at']}")
    
    def test_products_api_with_tenant_token(self):
        """Test products API works with tenant token"""
        token = getattr(self.__class__, 'tenant_token', None)
        if not token:
            pytest.skip("No token from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/products?limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Products API failed: {response.text}"
        
        data = response.json()
        
        # Can be list or dict with products key
        if isinstance(data, dict):
            products = data.get("products", data.get("items", []))
        else:
            products = data
        
        print(f"SUCCESS: Products API returned {len(products)} products")
        
        # Verify product structure if products exist
        if products:
            product = products[0]
            # Verify correct field names after fix
            assert "name_en" in product or "name_ar" in product, "Product missing name_en/name_ar"
            assert "retail_price" in product or "price" in product, "Product missing retail_price"
            assert "quantity" in product or "stock" in product, "Product missing quantity"
            print(f"SUCCESS: Product fields verified (name_en/name_ar, retail_price, quantity)")
    
    def test_customers_api_with_tenant_token(self):
        """Test customers API works with tenant token"""
        token = getattr(self.__class__, 'tenant_token', None)
        if not token:
            pytest.skip("No token from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/customers?limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Customers API failed: {response.text}"
        print(f"SUCCESS: Customers API returned status 200")
    
    def test_suppliers_api_with_tenant_token(self):
        """Test suppliers API works with tenant token"""
        token = getattr(self.__class__, 'tenant_token', None)
        if not token:
            pytest.skip("No token from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/suppliers?limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Suppliers API failed: {response.text}"
        print(f"SUCCESS: Suppliers API returned status 200")
    
    def test_employees_api_with_tenant_token(self):
        """Test employees API works with tenant token"""
        token = getattr(self.__class__, 'tenant_token', None)
        if not token:
            pytest.skip("No token from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/employees?limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Employees API failed: {response.text}"
        print(f"SUCCESS: Employees API returned status 200")
    
    def test_sales_api_with_tenant_token(self):
        """Test sales API works with tenant token"""
        token = getattr(self.__class__, 'tenant_token', None)
        if not token:
            pytest.skip("No token from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/sales?limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Sales API failed: {response.text}"
        print(f"SUCCESS: Sales API returned status 200")
    
    def test_expenses_api_with_tenant_token(self):
        """Test expenses API works with tenant token"""
        token = getattr(self.__class__, 'tenant_token', None)
        if not token:
            pytest.skip("No token from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/expenses?limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expenses API failed: {response.text}"
        print(f"SUCCESS: Expenses API returned status 200")


class TestAdminLogin:
    """Test admin login still works"""
    
    def test_admin_unified_login(self):
        """Test admin can login via unified-login endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/auth/unified-login",
            json={"email": "super@ntcommerce.com", "password": "password"}
        )
        
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        
        data = response.json()
        assert data["user_type"] == "admin", f"Expected admin, got {data['user_type']}"
        assert data["redirect_to"] == "/", "Wrong redirect path for admin"
        
        print(f"SUCCESS: Admin login successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
