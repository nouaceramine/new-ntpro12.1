"""
Test Suite: Multi-Tenant Data Isolation
=======================================
Critical bug fix verification: Products and customers created by one tenant 
should NOT be visible to other tenants.

Fix implemented: ContextVar + DB Proxy pattern
- Middleware extracts tenant_id from JWT and sets ContextVar
- _TenantDBProxy routes all db.collection calls to tenant-specific database
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN = {"email": "super@ntcommerce.com", "password": "password"}
TENANT_A = {"email": "tenanta@test.com", "password": "password123"}
TENANT_B = {"email": "tenantb@test.com", "password": "password123"}


class TestAuthentication:
    """Test unified login endpoint returns correct user types and tenant_ids"""
    
    def test_health_check(self):
        """Verify API is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "healthy", "Health status not healthy"
        print("PASS: Health check endpoint works")
    
    def test_super_admin_login(self):
        """Super Admin login returns user_type='admin' with super_admin role"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=SUPER_ADMIN)
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        
        assert "access_token" in data, "No access_token in response"
        assert data.get("user_type") == "admin", f"Expected user_type='admin', got '{data.get('user_type')}'"
        assert data.get("user", {}).get("role") == "super_admin", "Role should be super_admin"
        print(f"PASS: Super Admin login works - user_type={data.get('user_type')}, role={data.get('user', {}).get('role')}")
        return data["access_token"]
    
    def test_tenant_a_login(self):
        """Tenant A login returns user_type='tenant' with correct tenant_id"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_A)
        assert response.status_code == 200, f"Tenant A login failed: {response.text}"
        data = response.json()
        
        assert "access_token" in data, "No access_token in response"
        assert data.get("user_type") == "tenant", f"Expected user_type='tenant', got '{data.get('user_type')}'"
        assert data.get("user", {}).get("id"), "No tenant_id in user object"
        print(f"PASS: Tenant A login works - user_type={data.get('user_type')}, tenant_id={data.get('user', {}).get('id')}")
        return data["access_token"]
    
    def test_tenant_b_login(self):
        """Tenant B login returns user_type='tenant' with correct tenant_id"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_B)
        assert response.status_code == 200, f"Tenant B login failed: {response.text}"
        data = response.json()
        
        assert "access_token" in data, "No access_token in response"
        assert data.get("user_type") == "tenant", f"Expected user_type='tenant', got '{data.get('user_type')}'"
        assert data.get("user", {}).get("id"), "No tenant_id in user object"
        print(f"PASS: Tenant B login works - user_type={data.get('user_type')}, tenant_id={data.get('user', {}).get('id')}")
        return data["access_token"]


class TestSaasAdminAccess:
    """Test Super Admin can access SaaS management routes"""
    
    @pytest.fixture
    def super_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=SUPER_ADMIN)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_saas_tenants(self, super_admin_token):
        """Super Admin can access GET /api/saas/tenants"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        assert response.status_code == 200, f"Failed to get tenants: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: Super Admin can access /api/saas/tenants - Found {len(data)} tenants")
    
    def test_get_saas_plans(self, super_admin_token):
        """Super Admin can access GET /api/saas/plans"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/plans", headers=headers)
        assert response.status_code == 200, f"Failed to get plans: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: Super Admin can access /api/saas/plans - Found {len(data)} plans")
    
    def test_super_admin_cannot_see_tenant_products(self, super_admin_token):
        """Super Admin calling GET /api/products should NOT see tenant-specific products"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200, f"Failed to get products: {response.text}"
        data = response.json()
        
        # Super admin should see main_db products (which should be empty or only have main db products)
        # They should NOT see "Product_For_A_Only" or "Product_For_B_Only"
        product_names = [p.get("name_en", p.get("name_ar", "")) for p in data]
        
        # Check that tenant-specific products are NOT visible
        assert "Product_For_A_Only" not in str(product_names), \
            "CRITICAL: Super Admin can see Tenant A's product - DATA ISOLATION BROKEN"
        assert "Product_For_B_Only" not in str(product_names), \
            "CRITICAL: Super Admin can see Tenant B's product - DATA ISOLATION BROKEN"
        
        print(f"PASS: Super Admin cannot see tenant-specific products. Products in main_db: {len(data)}")


class TestProductDataIsolation:
    """Test that products are isolated between tenants - CRITICAL BUG FIX VERIFICATION"""
    
    @pytest.fixture
    def tenant_a_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_A)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def tenant_b_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_B)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_tenant_a_can_list_own_products(self, tenant_a_token):
        """Tenant A can list their own products"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200, f"Failed to get products: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: Tenant A can list products - Found {len(data)} products")
        
        # Check if Product_For_A_Only exists (should have been seeded)
        product_names = [p.get("name_en", "") for p in data]
        print(f"  Tenant A products: {product_names}")
        return data
    
    def test_tenant_b_can_list_own_products(self, tenant_b_token):
        """Tenant B can list their own products"""
        headers = {"Authorization": f"Bearer {tenant_b_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200, f"Failed to get products: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: Tenant B can list products - Found {len(data)} products")
        
        # Check if Product_For_B_Only exists (should have been seeded)
        product_names = [p.get("name_en", "") for p in data]
        print(f"  Tenant B products: {product_names}")
        return data
    
    def test_tenant_a_cannot_see_tenant_b_products(self, tenant_a_token, tenant_b_token):
        """CRITICAL: Tenant A should NOT see Tenant B's products"""
        # First get Tenant B's products
        headers_b = {"Authorization": f"Bearer {tenant_b_token}"}
        response_b = requests.get(f"{BASE_URL}/api/products", headers=headers_b)
        tenant_b_products = response_b.json()
        tenant_b_names = [p.get("name_en", "") for p in tenant_b_products]
        
        # Now get Tenant A's products
        headers_a = {"Authorization": f"Bearer {tenant_a_token}"}
        response_a = requests.get(f"{BASE_URL}/api/products", headers=headers_a)
        tenant_a_products = response_a.json()
        tenant_a_names = [p.get("name_en", "") for p in tenant_a_products]
        
        # Check that Tenant B's products are NOT in Tenant A's list
        for b_name in tenant_b_names:
            if b_name:  # Skip empty names
                assert b_name not in tenant_a_names, \
                    f"CRITICAL DATA LEAK: Tenant A can see Tenant B's product '{b_name}'"
        
        # Specifically check for Product_For_B_Only
        assert "Product_For_B_Only" not in tenant_a_names, \
            "CRITICAL DATA LEAK: Tenant A can see Product_For_B_Only"
        
        print(f"PASS: Tenant A cannot see Tenant B's products")
        print(f"  Tenant A sees: {tenant_a_names}")
        print(f"  Tenant B has: {tenant_b_names}")
    
    def test_tenant_b_cannot_see_tenant_a_products(self, tenant_a_token, tenant_b_token):
        """CRITICAL: Tenant B should NOT see Tenant A's products"""
        # First get Tenant A's products
        headers_a = {"Authorization": f"Bearer {tenant_a_token}"}
        response_a = requests.get(f"{BASE_URL}/api/products", headers=headers_a)
        tenant_a_products = response_a.json()
        tenant_a_names = [p.get("name_en", "") for p in tenant_a_products]
        
        # Now get Tenant B's products
        headers_b = {"Authorization": f"Bearer {tenant_b_token}"}
        response_b = requests.get(f"{BASE_URL}/api/products", headers=headers_b)
        tenant_b_products = response_b.json()
        tenant_b_names = [p.get("name_en", "") for p in tenant_b_products]
        
        # Check that Tenant A's products are NOT in Tenant B's list
        for a_name in tenant_a_names:
            if a_name:  # Skip empty names
                assert a_name not in tenant_b_names, \
                    f"CRITICAL DATA LEAK: Tenant B can see Tenant A's product '{a_name}'"
        
        # Specifically check for Product_For_A_Only
        assert "Product_For_A_Only" not in tenant_b_names, \
            "CRITICAL DATA LEAK: Tenant B can see Product_For_A_Only"
        
        print(f"PASS: Tenant B cannot see Tenant A's products")
        print(f"  Tenant B sees: {tenant_b_names}")
        print(f"  Tenant A has: {tenant_a_names}")
    
    def test_tenant_a_create_product_not_visible_to_tenant_b(self, tenant_a_token, tenant_b_token):
        """CRITICAL: Product created by Tenant A should NOT be visible to Tenant B"""
        # Tenant A creates a new product
        headers_a = {"Authorization": f"Bearer {tenant_a_token}"}
        new_product = {
            "name_en": "TEST_TenantA_Secret_Product",
            "name_ar": "منتج سري للمستأجر أ",
            "purchase_price": 100,
            "wholesale_price": 150,
            "retail_price": 200,
            "quantity": 10,
            "compatible_models": ["test"]
        }
        response_create = requests.post(f"{BASE_URL}/api/products", headers=headers_a, json=new_product)
        assert response_create.status_code == 200, f"Failed to create product: {response_create.text}"
        created_product = response_create.json()
        print(f"  Tenant A created product: {created_product.get('name_en')} (id={created_product.get('id')})")
        
        # Tenant B tries to list products
        headers_b = {"Authorization": f"Bearer {tenant_b_token}"}
        response_b = requests.get(f"{BASE_URL}/api/products", headers=headers_b)
        tenant_b_products = response_b.json()
        tenant_b_names = [p.get("name_en", "") for p in tenant_b_products]
        tenant_b_ids = [p.get("id", "") for p in tenant_b_products]
        
        # CRITICAL: Tenant B should NOT see the newly created product
        assert "TEST_TenantA_Secret_Product" not in tenant_b_names, \
            "CRITICAL DATA LEAK: Tenant B can see Tenant A's newly created product"
        assert created_product.get("id") not in tenant_b_ids, \
            "CRITICAL DATA LEAK: Tenant B can access Tenant A's product by ID"
        
        print(f"PASS: Product created by Tenant A is NOT visible to Tenant B")
        
        # Cleanup: Delete the test product
        delete_response = requests.delete(f"{BASE_URL}/api/products/{created_product['id']}", headers=headers_a)
        print(f"  Cleanup: Deleted test product (status={delete_response.status_code})")


class TestCustomerDataIsolation:
    """Test that customers are isolated between tenants"""
    
    @pytest.fixture
    def tenant_a_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_A)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def tenant_b_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_B)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_tenant_a_can_list_own_customers(self, tenant_a_token):
        """Tenant A can list their own customers"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        assert response.status_code == 200, f"Failed to get customers: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: Tenant A can list customers - Found {len(data)} customers")
        customer_names = [c.get("name", "") for c in data]
        print(f"  Tenant A customers: {customer_names}")
        return data
    
    def test_tenant_b_can_list_own_customers(self, tenant_b_token):
        """Tenant B can list their own customers"""
        headers = {"Authorization": f"Bearer {tenant_b_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        assert response.status_code == 200, f"Failed to get customers: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: Tenant B can list customers - Found {len(data)} customers")
        customer_names = [c.get("name", "") for c in data]
        print(f"  Tenant B customers: {customer_names}")
        return data
    
    def test_tenant_a_cannot_see_tenant_b_customers(self, tenant_a_token, tenant_b_token):
        """CRITICAL: Tenant A should NOT see Tenant B's customers"""
        # Get Tenant B's customers
        headers_b = {"Authorization": f"Bearer {tenant_b_token}"}
        response_b = requests.get(f"{BASE_URL}/api/customers", headers=headers_b)
        tenant_b_customers = response_b.json()
        tenant_b_names = [c.get("name", "") for c in tenant_b_customers]
        
        # Get Tenant A's customers
        headers_a = {"Authorization": f"Bearer {tenant_a_token}"}
        response_a = requests.get(f"{BASE_URL}/api/customers", headers=headers_a)
        tenant_a_customers = response_a.json()
        tenant_a_names = [c.get("name", "") for c in tenant_a_customers]
        
        # Check isolation
        for b_name in tenant_b_names:
            if b_name:
                assert b_name not in tenant_a_names, \
                    f"CRITICAL DATA LEAK: Tenant A can see Tenant B's customer '{b_name}'"
        
        print(f"PASS: Tenant A cannot see Tenant B's customers")
    
    def test_tenant_a_create_customer_not_visible_to_tenant_b(self, tenant_a_token, tenant_b_token):
        """CRITICAL: Customer created by Tenant A should NOT be visible to Tenant B"""
        # Tenant A creates a new customer
        headers_a = {"Authorization": f"Bearer {tenant_a_token}"}
        new_customer = {
            "name": "TEST_TenantA_Secret_Customer",
            "phone": "0555555555",
            "email": "secret_customer@tenanta.com"
        }
        response_create = requests.post(f"{BASE_URL}/api/customers", headers=headers_a, json=new_customer)
        assert response_create.status_code == 200, f"Failed to create customer: {response_create.text}"
        created_customer = response_create.json()
        print(f"  Tenant A created customer: {created_customer.get('name')} (id={created_customer.get('id')})")
        
        # Tenant B tries to list customers
        headers_b = {"Authorization": f"Bearer {tenant_b_token}"}
        response_b = requests.get(f"{BASE_URL}/api/customers", headers=headers_b)
        tenant_b_customers = response_b.json()
        tenant_b_names = [c.get("name", "") for c in tenant_b_customers]
        tenant_b_ids = [c.get("id", "") for c in tenant_b_customers]
        
        # CRITICAL: Tenant B should NOT see the newly created customer
        assert "TEST_TenantA_Secret_Customer" not in tenant_b_names, \
            "CRITICAL DATA LEAK: Tenant B can see Tenant A's newly created customer"
        assert created_customer.get("id") not in tenant_b_ids, \
            "CRITICAL DATA LEAK: Tenant B can access Tenant A's customer by ID"
        
        print(f"PASS: Customer created by Tenant A is NOT visible to Tenant B")
        
        # Cleanup: Delete the test customer
        delete_response = requests.delete(f"{BASE_URL}/api/customers/{created_customer['id']}", headers=headers_a)
        print(f"  Cleanup: Deleted test customer (status={delete_response.status_code})")


class TestTenantProductCRUD:
    """Test full CRUD operations for tenant products"""
    
    @pytest.fixture
    def tenant_a_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_A)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_create_product(self, tenant_a_token):
        """Tenant can create a product"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        product_data = {
            "name_en": "TEST_CRUD_Product",
            "name_ar": "منتج اختبار CRUD",
            "purchase_price": 50,
            "wholesale_price": 75,
            "retail_price": 100,
            "quantity": 20,
            "compatible_models": ["model1", "model2"]
        }
        response = requests.post(f"{BASE_URL}/api/products", headers=headers, json=product_data)
        assert response.status_code == 200, f"Failed to create product: {response.text}"
        data = response.json()
        assert data.get("id"), "No product ID returned"
        assert data.get("name_en") == "TEST_CRUD_Product"
        print(f"PASS: Create product - ID={data['id']}")
        return data["id"]
    
    def test_read_product(self, tenant_a_token):
        """Tenant can read their product"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        
        # First create
        product_data = {
            "name_en": "TEST_Read_Product",
            "name_ar": "منتج قراءة",
            "purchase_price": 30,
            "wholesale_price": 50,
            "retail_price": 70,
            "quantity": 5,
            "compatible_models": ["test"]
        }
        create_resp = requests.post(f"{BASE_URL}/api/products", headers=headers, json=product_data)
        product_id = create_resp.json()["id"]
        
        # Then read
        read_resp = requests.get(f"{BASE_URL}/api/products/{product_id}", headers=headers)
        assert read_resp.status_code == 200, f"Failed to read product: {read_resp.text}"
        data = read_resp.json()
        assert data.get("name_en") == "TEST_Read_Product"
        print(f"PASS: Read product - name_en={data['name_en']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/products/{product_id}", headers=headers)
    
    def test_update_product(self, tenant_a_token):
        """Tenant can update their product"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        
        # First create
        product_data = {
            "name_en": "TEST_Update_Product_Original",
            "name_ar": "منتج تحديث",
            "purchase_price": 40,
            "wholesale_price": 60,
            "retail_price": 80,
            "quantity": 10,
            "compatible_models": ["test"]
        }
        create_resp = requests.post(f"{BASE_URL}/api/products", headers=headers, json=product_data)
        product_id = create_resp.json()["id"]
        
        # Then update
        update_data = {"name_en": "TEST_Update_Product_Modified", "retail_price": 90}
        update_resp = requests.put(f"{BASE_URL}/api/products/{product_id}", headers=headers, json=update_data)
        assert update_resp.status_code == 200, f"Failed to update product: {update_resp.text}"
        
        # Verify update
        verify_resp = requests.get(f"{BASE_URL}/api/products/{product_id}", headers=headers)
        data = verify_resp.json()
        assert data.get("name_en") == "TEST_Update_Product_Modified"
        assert data.get("retail_price") == 90
        print(f"PASS: Update product - new name={data['name_en']}, new price={data['retail_price']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/products/{product_id}", headers=headers)
    
    def test_delete_product(self, tenant_a_token):
        """Tenant can delete their product"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        
        # First create
        product_data = {
            "name_en": "TEST_Delete_Product",
            "name_ar": "منتج حذف",
            "purchase_price": 25,
            "wholesale_price": 40,
            "retail_price": 55,
            "quantity": 3,
            "compatible_models": ["test"]
        }
        create_resp = requests.post(f"{BASE_URL}/api/products", headers=headers, json=product_data)
        product_id = create_resp.json()["id"]
        
        # Then delete
        delete_resp = requests.delete(f"{BASE_URL}/api/products/{product_id}", headers=headers)
        assert delete_resp.status_code == 200, f"Failed to delete product: {delete_resp.text}"
        
        # Verify deletion
        verify_resp = requests.get(f"{BASE_URL}/api/products/{product_id}", headers=headers)
        assert verify_resp.status_code == 404, "Product should not exist after deletion"
        print(f"PASS: Delete product - product no longer exists")


class TestTenantCustomerCRUD:
    """Test full CRUD operations for tenant customers"""
    
    @pytest.fixture
    def tenant_a_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_A)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_create_customer(self, tenant_a_token):
        """Tenant can create a customer"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        customer_data = {
            "name": "TEST_CRUD_Customer",
            "phone": "0666666666",
            "email": "crud_customer@test.com"
        }
        response = requests.post(f"{BASE_URL}/api/customers", headers=headers, json=customer_data)
        assert response.status_code == 200, f"Failed to create customer: {response.text}"
        data = response.json()
        assert data.get("id"), "No customer ID returned"
        assert data.get("name") == "TEST_CRUD_Customer"
        print(f"PASS: Create customer - ID={data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{data['id']}", headers=headers)
    
    def test_list_customers(self, tenant_a_token):
        """Tenant can list their customers"""
        headers = {"Authorization": f"Bearer {tenant_a_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        assert response.status_code == 200, f"Failed to list customers: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: List customers - Found {len(data)} customers")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
