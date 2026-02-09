"""
Comprehensive POS System Tests - Arabic/French Bilingual App
Tests: Login, Products, Customers, Suppliers, Sales, Daily Sessions, Reports
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "super@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "password"


class TestAuthentication:
    """Authentication Tests"""
    
    def test_login_super_admin(self):
        """Test login with super_admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "super_admin"
        print(f"✓ Login successful - user: {data['user']['name']}, role: {data['user']['role']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Authentication failed")


@pytest.fixture
def headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestProductFamilies:
    """Product Family CRUD Tests"""
    
    def test_get_product_families(self, headers):
        """Test getting all product families"""
        response = requests.get(f"{BASE_URL}/api/product-families", headers=headers)
        assert response.status_code == 200
        families = response.json()
        assert isinstance(families, list)
        print(f"✓ Found {len(families)} product families")
    
    def test_create_product_family_french(self, headers):
        """Test creating product family with French name"""
        family_data = {
            "name_en": f"TEST_Téléphones_{uuid.uuid4().hex[:8]}",
            "name_ar": "هواتف",
            "description_en": "Catégorie des téléphones mobiles",
            "description_ar": "فئة الهواتف المحمولة"
        }
        response = requests.post(f"{BASE_URL}/api/product-families", json=family_data, headers=headers)
        assert response.status_code == 200, f"Failed to create family: {response.text}"
        data = response.json()
        assert data["name_en"] == family_data["name_en"]
        print(f"✓ Created product family: {data['name_en']}")
        return data["id"]


class TestProducts:
    """Product CRUD Tests"""
    
    def test_get_products(self, headers):
        """Test getting all products"""
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)
        print(f"✓ Found {len(products)} products")
    
    def test_create_product_french(self, headers):
        """Test creating product with French name"""
        product_data = {
            "name_en": f"TEST_Écran_Samsung_{uuid.uuid4().hex[:8]}",
            "name_ar": "شاشة سامسونج",
            "description_en": "Écran de remplacement pour Samsung Galaxy",
            "description_ar": "شاشة بديلة لسامسونج جالاكسي",
            "purchase_price": 5000,
            "wholesale_price": 6000,
            "retail_price": 7500,
            "quantity": 10,
            "low_stock_threshold": 5
        }
        response = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=headers)
        assert response.status_code == 200, f"Failed to create product: {response.text}"
        data = response.json()
        assert data["name_en"] == product_data["name_en"]
        assert data["retail_price"] == 7500
        print(f"✓ Created product: {data['name_en']} - Price: {data['retail_price']} DZD")
        
        # Verify via GET
        get_response = requests.get(f"{BASE_URL}/api/products/{data['id']}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["name_en"] == product_data["name_en"]
        return data["id"]
    
    def test_update_product(self, headers):
        """Test updating product"""
        # First create a product
        product_data = {
            "name_en": f"TEST_Update_Product_{uuid.uuid4().hex[:8]}",
            "name_ar": "منتج للتحديث",
            "retail_price": 1000,
            "quantity": 5
        }
        create_resp = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=headers)
        assert create_resp.status_code == 200
        product_id = create_resp.json()["id"]
        
        # Update the product
        update_data = {"retail_price": 1500, "quantity": 20}
        update_resp = requests.put(f"{BASE_URL}/api/products/{product_id}", json=update_data, headers=headers)
        assert update_resp.status_code == 200
        
        # Verify update
        get_resp = requests.get(f"{BASE_URL}/api/products/{product_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["retail_price"] == 1500
        assert get_resp.json()["quantity"] == 20
        print(f"✓ Updated product - new price: 1500, new quantity: 20")


class TestCustomers:
    """Customer CRUD Tests"""
    
    def test_get_customers(self, headers):
        """Test getting all customers"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        assert response.status_code == 200
        customers = response.json()
        assert isinstance(customers, list)
        print(f"✓ Found {len(customers)} customers")
    
    def test_create_customer(self, headers):
        """Test creating a new customer"""
        customer_data = {
            "name": f"TEST_Client_{uuid.uuid4().hex[:8]}",
            "phone": "0555123456",
            "email": "test@example.com",
            "address": "123 Rue de Test, Alger"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=headers)
        assert response.status_code == 200, f"Failed to create customer: {response.text}"
        data = response.json()
        assert data["name"] == customer_data["name"]
        assert data["phone"] == customer_data["phone"]
        print(f"✓ Created customer: {data['name']}")
        
        # Verify via GET
        get_response = requests.get(f"{BASE_URL}/api/customers/{data['id']}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["name"] == customer_data["name"]
        return data["id"]


class TestSuppliers:
    """Supplier CRUD Tests"""
    
    def test_get_suppliers(self, headers):
        """Test getting all suppliers"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=headers)
        assert response.status_code == 200
        suppliers = response.json()
        assert isinstance(suppliers, list)
        print(f"✓ Found {len(suppliers)} suppliers")
    
    def test_create_supplier(self, headers):
        """Test creating a new supplier"""
        supplier_data = {
            "name": f"TEST_Fournisseur_{uuid.uuid4().hex[:8]}",
            "phone": "0661789012",
            "email": "supplier@example.com",
            "address": "Zone Industrielle, Oran"
        }
        response = requests.post(f"{BASE_URL}/api/suppliers", json=supplier_data, headers=headers)
        assert response.status_code == 200, f"Failed to create supplier: {response.text}"
        data = response.json()
        assert data["name"] == supplier_data["name"]
        print(f"✓ Created supplier: {data['name']}")
        return data["id"]


class TestDailySessions:
    """Daily Session Tests for POS"""
    
    def test_get_daily_sessions(self, headers):
        """Test getting daily sessions"""
        response = requests.get(f"{BASE_URL}/api/daily-sessions", headers=headers)
        assert response.status_code == 200
        sessions = response.json()
        assert isinstance(sessions, list)
        print(f"✓ Found {len(sessions)} daily sessions")
    
    def test_open_close_session_flow(self, headers):
        """Test opening and closing a POS session"""
        # Check current session
        current_resp = requests.get(f"{BASE_URL}/api/daily-sessions/current", headers=headers)
        
        if current_resp.status_code == 200 and current_resp.json():
            # Close existing session first
            session_id = current_resp.json()["id"]
            close_data = {
                "actual_cash": 0,
                "notes": "TEST session close"
            }
            close_resp = requests.post(f"{BASE_URL}/api/daily-sessions/{session_id}/close", json=close_data, headers=headers)
            print(f"✓ Closed existing session: {session_id}")
        
        # Open new session
        open_data = {"opening_cash": 5000}
        open_resp = requests.post(f"{BASE_URL}/api/daily-sessions/open", json=open_data, headers=headers)
        assert open_resp.status_code == 200, f"Failed to open session: {open_resp.text}"
        session = open_resp.json()
        assert session["status"] == "open"
        assert session["opening_cash"] == 5000
        print(f"✓ Opened new session with opening cash: 5000 DZD")
        
        # Close the session
        close_data = {"actual_cash": 5000, "notes": "TEST session"}
        close_resp = requests.post(f"{BASE_URL}/api/daily-sessions/{session['id']}/close", json=close_data, headers=headers)
        assert close_resp.status_code == 200, f"Failed to close session: {close_resp.text}"
        print(f"✓ Closed session successfully")


class TestSales:
    """Sales Tests"""
    
    def test_get_sales(self, headers):
        """Test getting all sales"""
        response = requests.get(f"{BASE_URL}/api/sales", headers=headers)
        assert response.status_code == 200
        sales = response.json()
        assert isinstance(sales, list)
        print(f"✓ Found {len(sales)} sales")
    
    def test_create_sale_full_flow(self, headers):
        """Test complete sale flow: Create product -> Open session -> Make sale"""
        # 1. Create a test product
        product_data = {
            "name_en": f"TEST_Sale_Product_{uuid.uuid4().hex[:8]}",
            "name_ar": "منتج للبيع",
            "retail_price": 1000,
            "quantity": 50
        }
        prod_resp = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=headers)
        assert prod_resp.status_code == 200
        product = prod_resp.json()
        print(f"✓ Created test product: {product['name_en']}")
        
        # 2. Close any existing session first
        current_resp = requests.get(f"{BASE_URL}/api/daily-sessions/current", headers=headers)
        if current_resp.status_code == 200 and current_resp.json():
            session_id = current_resp.json()["id"]
            requests.post(f"{BASE_URL}/api/daily-sessions/{session_id}/close", 
                         json={"actual_cash": 0}, headers=headers)
        
        # 3. Open a new session
        open_resp = requests.post(f"{BASE_URL}/api/daily-sessions/open", 
                                 json={"opening_cash": 1000}, headers=headers)
        assert open_resp.status_code == 200
        session = open_resp.json()
        print(f"✓ Opened POS session")
        
        # 4. Create sale
        sale_data = {
            "items": [{
                "product_id": product["id"],
                "product_name": product["name_en"],
                "quantity": 2,
                "unit_price": 1000,
                "discount": 0,
                "total": 2000
            }],
            "subtotal": 2000,
            "discount": 0,
            "total": 2000,
            "paid_amount": 2000,
            "payment_method": "cash",
            "payment_type": "cash"
        }
        sale_resp = requests.post(f"{BASE_URL}/api/sales", json=sale_data, headers=headers)
        assert sale_resp.status_code == 200, f"Failed to create sale: {sale_resp.text}"
        sale = sale_resp.json()
        assert sale["total"] == 2000
        assert sale["status"] == "paid"
        print(f"✓ Created sale - Invoice: {sale['invoice_number']}, Total: {sale['total']} DZD")
        
        # 5. Verify product stock decreased
        prod_get = requests.get(f"{BASE_URL}/api/products/{product['id']}", headers=headers)
        assert prod_get.status_code == 200
        assert prod_get.json()["quantity"] == 48  # 50 - 2
        print(f"✓ Product stock updated: 50 -> 48")
        
        # 6. Close session
        close_resp = requests.post(f"{BASE_URL}/api/daily-sessions/{session['id']}/close",
                                  json={"actual_cash": 3000}, headers=headers)
        assert close_resp.status_code == 200
        print(f"✓ Closed session")
        
        return sale["id"]


class TestNotifications:
    """Notification Tests"""
    
    def test_get_notifications(self, headers):
        """Test getting notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        assert response.status_code == 200
        notifications = response.json()
        assert isinstance(notifications, list)
        print(f"✓ Found {len(notifications)} notifications")


class TestReports:
    """Reports Tests"""
    
    def test_get_stats(self, headers):
        """Test getting stats"""
        response = requests.get(f"{BASE_URL}/api/stats", headers=headers)
        assert response.status_code == 200
        stats = response.json()
        assert "products" in stats or "sales" in stats or "customers" in stats
        print(f"✓ Stats retrieved successfully")
    
    def test_sales_stats(self, headers):
        """Test getting sales stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/sales-stats", headers=headers)
        assert response.status_code == 200
        print(f"✓ Sales stats retrieved successfully")


class TestPurchases:
    """Purchase Order Tests"""
    
    def test_get_purchases(self, headers):
        """Test getting all purchases"""
        response = requests.get(f"{BASE_URL}/api/purchases", headers=headers)
        assert response.status_code == 200
        purchases = response.json()
        assert isinstance(purchases, list)
        print(f"✓ Found {len(purchases)} purchases")


class TestSettings:
    """Settings Tests"""
    
    def test_get_settings(self, headers):
        """Test getting settings"""
        response = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        assert response.status_code == 200
        print(f"✓ Settings retrieved successfully")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_products(self, headers):
        """Cleanup TEST_ prefixed products"""
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        if response.status_code == 200:
            products = response.json()
            deleted = 0
            for p in products:
                if p.get("name_en", "").startswith("TEST_"):
                    del_resp = requests.delete(f"{BASE_URL}/api/products/{p['id']}", headers=headers)
                    if del_resp.status_code == 200:
                        deleted += 1
            print(f"✓ Cleaned up {deleted} test products")
    
    def test_cleanup_test_families(self, headers):
        """Cleanup TEST_ prefixed families"""
        response = requests.get(f"{BASE_URL}/api/product-families", headers=headers)
        if response.status_code == 200:
            families = response.json()
            deleted = 0
            for f in families:
                if f.get("name_en", "").startswith("TEST_"):
                    del_resp = requests.delete(f"{BASE_URL}/api/product-families/{f['id']}", headers=headers)
                    if del_resp.status_code == 200:
                        deleted += 1
            print(f"✓ Cleaned up {deleted} test families")
    
    def test_cleanup_test_customers(self, headers):
        """Cleanup TEST_ prefixed customers"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        if response.status_code == 200:
            customers = response.json()
            deleted = 0
            for c in customers:
                if c.get("name", "").startswith("TEST_"):
                    del_resp = requests.delete(f"{BASE_URL}/api/customers/{c['id']}", headers=headers)
                    if del_resp.status_code == 200:
                        deleted += 1
            print(f"✓ Cleaned up {deleted} test customers")
    
    def test_cleanup_test_suppliers(self, headers):
        """Cleanup TEST_ prefixed suppliers"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=headers)
        if response.status_code == 200:
            suppliers = response.json()
            deleted = 0
            for s in suppliers:
                if s.get("name", "").startswith("TEST_"):
                    del_resp = requests.delete(f"{BASE_URL}/api/suppliers/{s['id']}", headers=headers)
                    if del_resp.status_code == 200:
                        deleted += 1
            print(f"✓ Cleaned up {deleted} test suppliers")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
