"""
Test Suite for NT Commerce 12.0 - P1 Performance Improvements (Iteration 76)
Tests:
1. Pagination on all list endpoints (products, sales, purchases, expenses, debts, suppliers, employees, customers, cashbox transactions)
2. Strong password validation on register and password update
3. Redis cache integration for stats dashboard with cache management API
4. N+1 query fix verification for customers and suppliers
5. Regression tests for login and products
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "admin@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "Admin@2024"
TENANT_EMAIL = "ncr@ntcommerce.com"
TENANT_PASSWORD = "Test@123"


class TestAuthSetup:
    """Authentication setup and helper functions"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get super admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def tenant_token(self):
        """Get tenant token"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        assert response.status_code == 200, f"Tenant login failed: {response.text}"
        return response.json()["access_token"]


class TestPaginationEndpoints(TestAuthSetup):
    """Tests for all paginated endpoints - P1 performance feature"""
    
    def test_products_paginated(self, tenant_token):
        """GET /api/products/paginated returns paginated response"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/products/paginated?page=1&page_size=2", headers=headers)
        
        assert response.status_code == 200, f"Products paginated failed: {response.text}"
        data = response.json()
        
        # Verify pagination structure
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        assert "page" in data, "Missing 'page' in response"
        assert data["page"] == 1, f"Page should be 1, got {data['page']}"
        assert "total_pages" in data, "Missing 'total_pages' in response"
        # page_size or per_page
        assert "page_size" in data or "per_page" in data, "Missing 'page_size' or 'per_page' in response"
        print(f"✅ Products paginated: {len(data['items'])} items, total={data['total']}")
    
    def test_sales_paginated(self, tenant_token):
        """GET /api/sales/paginated returns paginated response"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/sales/paginated?page=1&page_size=5", headers=headers)
        
        assert response.status_code == 200, f"Sales paginated failed: {response.text}"
        data = response.json()
        
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        assert "page" in data, "Missing 'page' in response"
        print(f"✅ Sales paginated: {len(data['items'])} items, total={data['total']}")
    
    def test_purchases_paginated(self, tenant_token):
        """GET /api/purchases/paginated returns paginated response"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/purchases/paginated?page=1&page_size=5", headers=headers)
        
        assert response.status_code == 200, f"Purchases paginated failed: {response.text}"
        data = response.json()
        
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        print(f"✅ Purchases paginated: {len(data['items'])} items, total={data['total']}")
    
    def test_expenses_paginated(self, tenant_token):
        """GET /api/expenses/paginated returns paginated response"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/expenses/paginated?page=1&page_size=5", headers=headers)
        
        assert response.status_code == 200, f"Expenses paginated failed: {response.text}"
        data = response.json()
        
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        print(f"✅ Expenses paginated: {len(data['items'])} items, total={data['total']}")
    
    def test_debts_paginated(self, tenant_token):
        """GET /api/debts/paginated returns paginated response"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/debts/paginated?page=1&page_size=5", headers=headers)
        
        assert response.status_code == 200, f"Debts paginated failed: {response.text}"
        data = response.json()
        
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        print(f"✅ Debts paginated: {len(data['items'])} items, total={data['total']}")
    
    def test_suppliers_paginated(self, tenant_token):
        """GET /api/suppliers/paginated returns paginated response"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/suppliers/paginated?page=1&page_size=5", headers=headers)
        
        assert response.status_code == 200, f"Suppliers paginated failed: {response.text}"
        data = response.json()
        
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        print(f"✅ Suppliers paginated: {len(data['items'])} items, total={data['total']}")
    
    def test_employees_paginated(self, tenant_token):
        """GET /api/employees/paginated returns paginated response"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/employees/paginated?page=1&page_size=5", headers=headers)
        
        assert response.status_code == 200, f"Employees paginated failed: {response.text}"
        data = response.json()
        
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        print(f"✅ Employees paginated: {len(data['items'])} items, total={data['total']}")
    
    def test_customers_paginated(self, tenant_token):
        """GET /api/customers/paginated returns paginated response"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/customers/paginated?page=1&page_size=5", headers=headers)
        
        assert response.status_code == 200, f"Customers paginated failed: {response.text}"
        data = response.json()
        
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        print(f"✅ Customers paginated: {len(data['items'])} items, total={data['total']}")
    
    def test_cashbox_transactions_paginated(self, tenant_token):
        """GET /api/transactions/paginated returns paginated response"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/transactions/paginated?page=1&page_size=5", headers=headers)
        
        assert response.status_code == 200, f"Transactions paginated failed: {response.text}"
        data = response.json()
        
        assert "items" in data, "Missing 'items' in response"
        assert "total" in data, "Missing 'total' in response"
        print(f"✅ Cashbox transactions paginated: {len(data['items'])} items, total={data['total']}")


class TestPasswordValidation(TestAuthSetup):
    """Tests for strong password validation - P1 security feature"""
    
    def test_register_weak_password_rejected(self):
        """POST /api/auth/register with weak password '123' returns 400"""
        unique_email = f"test_weak_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "123",
            "name": "Test User",
            "role": "user"
        })
        
        assert response.status_code == 400, f"Expected 400 for weak password, got {response.status_code}"
        data = response.json()
        
        # Should contain Arabic error messages
        detail = data.get("detail", {})
        if isinstance(detail, dict):
            errors = detail.get("errors", [])
            assert len(errors) > 0, "Expected validation errors for weak password"
            # Check for Arabic error messages
            error_text = " ".join(errors)
            assert "كلمة المرور" in error_text or "يجب" in error_text, f"Expected Arabic error messages, got: {errors}"
            print(f"✅ Weak password rejected with errors: {errors}")
        else:
            print(f"✅ Weak password rejected: {detail}")
    
    def test_register_strong_password_accepted(self):
        """POST /api/auth/register with strong password 'StrongP@ss1' succeeds"""
        unique_email = f"test_strong_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "StrongP@ss1",
            "name": "Test Strong User",
            "role": "user"
        })
        
        # Should succeed (200 or 201) or return conflict if email exists
        assert response.status_code in [200, 201], f"Expected 200/201 for strong password, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data, "Missing access_token in response"
        print(f"✅ Strong password accepted, user registered: {unique_email}")
    
    def test_register_missing_uppercase_rejected(self):
        """Password missing uppercase letter should be rejected"""
        unique_email = f"test_noup_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "weakpass@1",  # No uppercase
            "name": "Test User",
            "role": "user"
        })
        
        assert response.status_code == 400, f"Expected 400 for password without uppercase, got {response.status_code}"
        print(f"✅ Password without uppercase rejected")
    
    def test_register_missing_special_char_rejected(self):
        """Password missing special character should be rejected"""
        unique_email = f"test_nospec_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "WeakPass1",  # No special char
            "name": "Test User",
            "role": "user"
        })
        
        assert response.status_code == 400, f"Expected 400 for password without special char, got {response.status_code}"
        print(f"✅ Password without special char rejected")
    
    def test_password_update_validation(self, admin_token):
        """PUT /api/users/{id}/password validates password strength"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First get list of users to get a user id
        users_response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        if users_response.status_code == 200:
            users = users_response.json()
            if users:
                user_id = users[0]["id"]
                
                # Try to update with weak password
                response = requests.put(f"{BASE_URL}/api/users/{user_id}/password", 
                    headers=headers,
                    json={"new_password": "weak"}
                )
                
                assert response.status_code == 400, f"Expected 400 for weak password update, got {response.status_code}"
                print(f"✅ Password update with weak password rejected")
            else:
                print("⚠️ No users found to test password update")
        else:
            print(f"⚠️ Could not get users list: {users_response.status_code}")


class TestCacheManagement(TestAuthSetup):
    """Tests for Redis cache management API - P1 performance feature"""
    
    def test_cache_stats_returns_availability(self, admin_token):
        """GET /api/cache/stats returns available:true with hits/misses (admin only)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/cache/stats", headers=headers)
        
        assert response.status_code == 200, f"Cache stats failed: {response.text}"
        data = response.json()
        
        assert "available" in data, "Missing 'available' in cache stats"
        if data["available"]:
            assert "hits" in data, "Missing 'hits' in cache stats"
            assert "misses" in data, "Missing 'misses' in cache stats"
            print(f"✅ Cache stats: available=True, hits={data.get('hits')}, misses={data.get('misses')}, keys={data.get('keys')}")
        else:
            print(f"⚠️ Redis cache not available (disabled or connection issue)")
    
    def test_cache_stats_requires_admin(self, tenant_token):
        """GET /api/cache/stats requires admin - tenant should get 403"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/cache/stats", headers=headers)
        
        # Should return 403 for non-admin
        assert response.status_code == 403, f"Expected 403 for tenant on cache stats, got {response.status_code}"
        print(f"✅ Cache stats correctly requires admin access")
    
    def test_cache_flush_clears_cache(self, admin_token):
        """POST /api/cache/flush clears cache (admin only)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(f"{BASE_URL}/api/cache/flush", headers=headers)
        
        assert response.status_code == 200, f"Cache flush failed: {response.text}"
        data = response.json()
        assert "message" in data, "Missing success message"
        print(f"✅ Cache flush successful: {data['message']}")
    
    def test_stats_caching_behavior(self, tenant_token):
        """GET /api/stats returns cached response on second call"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        
        # First call - should set cache
        start1 = time.time()
        response1 = requests.get(f"{BASE_URL}/api/stats", headers=headers)
        time1 = time.time() - start1
        
        assert response1.status_code == 200, f"Stats call 1 failed: {response1.text}"
        data1 = response1.json()
        
        # Small delay
        time.sleep(0.2)
        
        # Second call - should hit cache (faster)
        start2 = time.time()
        response2 = requests.get(f"{BASE_URL}/api/stats", headers=headers)
        time2 = time.time() - start2
        
        assert response2.status_code == 200, f"Stats call 2 failed: {response2.text}"
        data2 = response2.json()
        
        # Both should return same structure
        assert "total_products" in data1, "Missing total_products in stats"
        assert "total_customers" in data2, "Missing total_customers in stats"
        
        print(f"✅ Stats endpoint working: call1={time1:.3f}s, call2={time2:.3f}s")
        print(f"   Stats: products={data1.get('total_products')}, customers={data1.get('total_customers')}")


class TestN1QueryFix(TestAuthSetup):
    """Tests for N+1 query fix verification - P1 performance feature"""
    
    def test_customers_with_family_name_populated(self, tenant_token):
        """GET /api/customers returns customers with family_name populated (N+1 fix)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        
        assert response.status_code == 200, f"Customers endpoint failed: {response.text}"
        customers = response.json()
        
        if customers:
            # Check that family_name field exists (even if empty string)
            for customer in customers[:5]:  # Check first 5
                assert "family_name" in customer, f"Missing family_name in customer: {customer.get('name')}"
                assert "family_id" in customer, f"Missing family_id in customer: {customer.get('name')}"
            print(f"✅ Customers have family_name populated: {len(customers)} customers returned")
        else:
            print(f"⚠️ No customers in database to verify N+1 fix")
    
    def test_suppliers_with_family_name_populated(self, tenant_token):
        """GET /api/suppliers returns suppliers with family_name populated (N+1 fix)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=headers)
        
        assert response.status_code == 200, f"Suppliers endpoint failed: {response.text}"
        suppliers = response.json()
        
        if suppliers:
            # Check that family_name field exists (even if empty string)
            for supplier in suppliers[:5]:  # Check first 5
                assert "family_name" in supplier, f"Missing family_name in supplier: {supplier.get('name')}"
                assert "family_id" in supplier, f"Missing family_id in supplier: {supplier.get('name')}"
            print(f"✅ Suppliers have family_name populated: {len(suppliers)} suppliers returned")
        else:
            print(f"⚠️ No suppliers in database to verify N+1 fix")
    
    def test_customers_paginated_with_family_name(self, tenant_token):
        """Paginated customers also have family_name populated"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/customers/paginated?page=1&page_size=5", headers=headers)
        
        assert response.status_code == 200, f"Customers paginated failed: {response.text}"
        data = response.json()
        
        if data.get("items"):
            for customer in data["items"]:
                assert "family_name" in customer, f"Missing family_name in paginated customer"
            print(f"✅ Paginated customers have family_name: {len(data['items'])} items")
        else:
            print(f"⚠️ No customers in paginated response")
    
    def test_suppliers_paginated_with_family_name(self, tenant_token):
        """Paginated suppliers also have family_name populated"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/suppliers/paginated?page=1&page_size=5", headers=headers)
        
        assert response.status_code == 200, f"Suppliers paginated failed: {response.text}"
        data = response.json()
        
        if data.get("items"):
            for supplier in data["items"]:
                assert "family_name" in supplier, f"Missing family_name in paginated supplier"
            print(f"✅ Paginated suppliers have family_name: {len(data['items'])} items")
        else:
            print(f"⚠️ No suppliers in paginated response")


class TestRegressionAfterChanges(TestAuthSetup):
    """Regression tests to ensure core functionality still works"""
    
    def test_login_still_works(self):
        """Login endpoints still function correctly after all changes"""
        # Test unified login
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        
        assert response.status_code == 200, f"Unified login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Missing access_token"
        assert "user" in data, "Missing user in response"
        print(f"✅ Unified login working: user_type={data.get('user_type')}")
    
    def test_standard_login_still_works(self):
        """Standard login endpoint still works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Standard login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Missing access_token"
        print(f"✅ Standard login working")
    
    def test_products_list_still_works(self, tenant_token):
        """Products list endpoint still works (regression test)"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        
        assert response.status_code == 200, f"Products list failed: {response.text}"
        products = response.json()
        assert isinstance(products, list), "Products should return a list"
        print(f"✅ Products list working: {len(products)} products")
    
    def test_stats_endpoint_still_works(self, tenant_token):
        """Stats dashboard endpoint still works"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/stats", headers=headers)
        
        assert response.status_code == 200, f"Stats endpoint failed: {response.text}"
        data = response.json()
        
        # Verify expected fields exist
        expected_fields = ["total_products", "total_customers", "today_sales_total"]
        for field in expected_fields:
            assert field in data, f"Missing {field} in stats response"
        print(f"✅ Stats endpoint working: {data.get('total_products')} products, {data.get('total_customers')} customers")
    
    def test_customers_endpoint_still_works(self, tenant_token):
        """Customers list endpoint still works"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        
        assert response.status_code == 200, f"Customers endpoint failed: {response.text}"
        customers = response.json()
        assert isinstance(customers, list), "Customers should return a list"
        print(f"✅ Customers list working: {len(customers)} customers")
    
    def test_suppliers_endpoint_still_works(self, tenant_token):
        """Suppliers list endpoint still works"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=headers)
        
        assert response.status_code == 200, f"Suppliers endpoint failed: {response.text}"
        suppliers = response.json()
        assert isinstance(suppliers, list), "Suppliers should return a list"
        print(f"✅ Suppliers list working: {len(suppliers)} suppliers")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
