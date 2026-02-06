"""
Backend Tests for POS Features: Delivery, Credit Sales, Customer Debt
Tests: /api/delivery/wilayas, /api/delivery/fee, /api/customers/{id}/debt, /api/customers/{id}/debt/pay, /api/debts/summary
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDeliveryEndpoints:
    """Test Algeria delivery wilayas and fee calculation"""
    
    def test_get_all_wilayas(self):
        """GET /api/delivery/wilayas - Should return 58 wilayas"""
        response = requests.get(f"{BASE_URL}/api/delivery/wilayas")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 58, f"Expected 58 wilayas, got {len(data)}"
        
        # Verify structure of first wilaya
        first_wilaya = data[0]
        assert "code" in first_wilaya
        assert "name_ar" in first_wilaya
        assert "name_en" in first_wilaya
        assert "desk_fee" in first_wilaya
        assert "home_fee" in first_wilaya
        print(f"✓ Found {len(data)} wilayas")
    
    def test_wilaya_algiers_fees(self):
        """Verify Algiers (code 16) has correct fees: desk=250, home=400"""
        response = requests.get(f"{BASE_URL}/api/delivery/wilayas")
        assert response.status_code == 200
        
        wilayas = response.json()
        algiers = next((w for w in wilayas if w["code"] == "16"), None)
        
        assert algiers is not None, "Algiers (code 16) not found"
        assert algiers["name_ar"] == "الجزائر", f"Expected 'الجزائر', got '{algiers['name_ar']}'"
        assert algiers["desk_fee"] == 250, f"Expected desk_fee=250, got {algiers['desk_fee']}"
        assert algiers["home_fee"] == 400, f"Expected home_fee=400, got {algiers['home_fee']}"
        print(f"✓ Algiers fees correct: desk={algiers['desk_fee']}, home={algiers['home_fee']}")
    
    def test_wilaya_tamanrasset_fees(self):
        """Verify Tamanrasset (code 11) has high fees: desk=800, home=1000"""
        response = requests.get(f"{BASE_URL}/api/delivery/wilayas")
        assert response.status_code == 200
        
        wilayas = response.json()
        tamanrasset = next((w for w in wilayas if w["code"] == "11"), None)
        
        assert tamanrasset is not None
        assert tamanrasset["desk_fee"] == 800
        assert tamanrasset["home_fee"] == 1000
        print(f"✓ Tamanrasset (remote) fees correct: desk={tamanrasset['desk_fee']}, home={tamanrasset['home_fee']}")
    
    def test_delivery_fee_calculation_desk(self):
        """GET /api/delivery/fee - Calculate desk delivery fee"""
        response = requests.get(f"{BASE_URL}/api/delivery/fee?wilaya_code=16&delivery_type=desk")
        assert response.status_code == 200
        
        data = response.json()
        assert data["wilaya_code"] == "16"
        assert data["delivery_type"] == "desk"
        assert data["fee"] == 250, f"Expected fee=250, got {data['fee']}"
        print(f"✓ Delivery fee calculation correct: {data['fee']} DZD for desk delivery")
    
    def test_delivery_fee_calculation_home(self):
        """GET /api/delivery/fee - Calculate home delivery fee"""
        response = requests.get(f"{BASE_URL}/api/delivery/fee?wilaya_code=16&delivery_type=home")
        assert response.status_code == 200
        
        data = response.json()
        assert data["fee"] == 400, f"Expected fee=400, got {data['fee']}"
        print(f"✓ Home delivery fee: {data['fee']} DZD")
    
    def test_delivery_fee_invalid_wilaya(self):
        """GET /api/delivery/fee - Invalid wilaya returns 404"""
        response = requests.get(f"{BASE_URL}/api/delivery/fee?wilaya_code=99&delivery_type=desk")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid wilaya returns 404")


class TestAuthAndSetup:
    """Test authentication and get token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@admin.com",
            "password": "admin"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json()["access_token"]
        print(f"✓ Login successful, got token")
        return token
    
    def test_login(self, auth_token):
        """Verify login works"""
        assert auth_token is not None and len(auth_token) > 0
        print("✓ Auth token obtained")


class TestCustomerDebtFlow:
    """Test customer debt tracking and payment"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@admin.com",
            "password": "admin"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_customer(self, auth_token):
        """Create a test customer for debt testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        customer_data = {
            "name": "TEST_DebtCustomer",
            "phone": "0555123456",
            "address": "Test Address",
            "email": "test@debt.com"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=headers)
        assert response.status_code == 200 or response.status_code == 201
        customer = response.json()
        print(f"✓ Created test customer: {customer['name']}")
        return customer
    
    def test_customer_debt_no_debt(self, auth_token, test_customer):
        """GET /api/customers/{id}/debt - New customer has 0 debt"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/customers/{test_customer['id']}/debt", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_debt" in data
        assert data["total_debt"] >= 0  # Could be 0 for new customer
        print(f"✓ Customer debt endpoint working, total_debt: {data['total_debt']}")
    
    def test_customer_debt_not_found(self, auth_token):
        """GET /api/customers/{id}/debt - Non-existent customer returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/customers/nonexistent-id/debt", headers=headers)
        assert response.status_code == 404
        print("✓ Non-existent customer returns 404")


class TestDebtsSummary:
    """Test debt summary endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@admin.com",
            "password": "admin"
        })
        return response.json()["access_token"]
    
    def test_debts_summary(self, auth_token):
        """GET /api/debts/summary - Get all customer debts summary"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/debts/summary", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_outstanding" in data
        assert "customers_with_debt" in data
        assert "debts" in data
        assert isinstance(data["debts"], list)
        print(f"✓ Debts summary: total_outstanding={data['total_outstanding']}, customers_with_debt={data['customers_with_debt']}")


class TestCreditSale:
    """Test POS credit sale (debt-based sale)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@admin.com",
            "password": "admin"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_customer(self, auth_token):
        """Create a test customer for credit sale"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        customer_data = {
            "name": "TEST_CreditSaleCustomer",
            "phone": "0555987654"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=headers)
        return response.json()
    
    @pytest.fixture(scope="class")
    def test_product(self, auth_token):
        """Create a test product for sales"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        product_data = {
            "name_ar": "منتج اختبار الدين",
            "name_en": "TEST_CreditProduct",
            "retail_price": 1000,
            "wholesale_price": 800,
            "purchase_price": 500,
            "quantity": 100,
            "low_stock_threshold": 5
        }
        response = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=headers)
        return response.json()
    
    def test_credit_sale_requires_customer(self, auth_token, test_product):
        """Credit sale without customer should fail"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        sale_data = {
            "customer_id": None,  # No customer
            "items": [{
                "product_id": test_product["id"],
                "product_name": test_product["name_en"],
                "quantity": 1,
                "unit_price": 1000,
                "discount": 0,
                "total": 1000
            }],
            "subtotal": 1000,
            "discount": 0,
            "total": 1000,
            "paid_amount": 0,
            "payment_method": "cash",
            "payment_type": "credit"  # Credit sale
        }
        response = requests.post(f"{BASE_URL}/api/sales", json=sale_data, headers=headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Credit sale without customer correctly rejected")
    
    def test_credit_sale_creates_debt(self, auth_token, test_customer, test_product):
        """Credit sale should create debt for customer"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        sale_data = {
            "customer_id": test_customer["id"],
            "items": [{
                "product_id": test_product["id"],
                "product_name": test_product["name_en"],
                "quantity": 1,
                "unit_price": 1000,
                "discount": 0,
                "total": 1000
            }],
            "subtotal": 1000,
            "discount": 0,
            "total": 1000,
            "paid_amount": 0,
            "payment_method": "cash",
            "payment_type": "credit"  # Credit/debt sale
        }
        response = requests.post(f"{BASE_URL}/api/sales", json=sale_data, headers=headers)
        assert response.status_code == 200, f"Sale failed: {response.text}"
        
        sale = response.json()
        assert sale["payment_type"] == "credit"
        assert sale["debt_amount"] == 1000, f"Expected debt_amount=1000, got {sale.get('debt_amount')}"
        assert sale["status"] == "unpaid", f"Expected status=unpaid, got {sale.get('status')}"
        print(f"✓ Credit sale created with debt_amount={sale['debt_amount']}")
        
        # Verify customer debt is updated
        debt_response = requests.get(f"{BASE_URL}/api/customers/{test_customer['id']}/debt", headers=headers)
        assert debt_response.status_code == 200
        debt_data = debt_response.json()
        assert debt_data["total_debt"] >= 1000, f"Expected debt >= 1000, got {debt_data['total_debt']}"
        print(f"✓ Customer debt updated: {debt_data['total_debt']}")


class TestPartialPaymentSale:
    """Test partial payment sale flow"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@admin.com",
            "password": "admin"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_customer(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/customers", json={
            "name": "TEST_PartialPayCustomer",
            "phone": "0555111222"
        }, headers=headers)
        return response.json()
    
    @pytest.fixture(scope="class")
    def test_product(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/products", json={
            "name_ar": "منتج دفع جزئي",
            "name_en": "TEST_PartialPayProduct",
            "retail_price": 2000,
            "wholesale_price": 1500,
            "purchase_price": 1000,
            "quantity": 50
        }, headers=headers)
        return response.json()
    
    def test_partial_payment_sale(self, auth_token, test_customer, test_product):
        """Partial payment creates partial debt"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        sale_data = {
            "customer_id": test_customer["id"],
            "items": [{
                "product_id": test_product["id"],
                "product_name": test_product["name_en"],
                "quantity": 1,
                "unit_price": 2000,
                "discount": 0,
                "total": 2000
            }],
            "subtotal": 2000,
            "discount": 0,
            "total": 2000,
            "paid_amount": 1000,  # Partial payment
            "payment_method": "cash",
            "payment_type": "partial"
        }
        response = requests.post(f"{BASE_URL}/api/sales", json=sale_data, headers=headers)
        assert response.status_code == 200, f"Sale failed: {response.text}"
        
        sale = response.json()
        assert sale["payment_type"] == "partial"
        assert sale["paid_amount"] == 1000
        assert sale["debt_amount"] == 1000, f"Expected debt_amount=1000, got {sale.get('debt_amount')}"
        assert sale["status"] == "partial", f"Expected status=partial, got {sale.get('status')}"
        print(f"✓ Partial payment sale: paid={sale['paid_amount']}, debt={sale['debt_amount']}")


class TestSaleWithDelivery:
    """Test POS sale with delivery"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@admin.com",
            "password": "admin"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_product(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/products", json={
            "name_ar": "منتج توصيل",
            "name_en": "TEST_DeliveryProduct",
            "retail_price": 500,
            "wholesale_price": 400,
            "purchase_price": 300,
            "quantity": 100
        }, headers=headers)
        return response.json()
    
    def test_sale_with_delivery_desk(self, auth_token, test_product):
        """Sale with desk delivery adds delivery fee to total"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        sale_data = {
            "customer_id": None,  # Walk-in customer
            "items": [{
                "product_id": test_product["id"],
                "product_name": test_product["name_en"],
                "quantity": 1,
                "unit_price": 500,
                "discount": 0,
                "total": 500
            }],
            "subtotal": 500,
            "discount": 0,
            "total": 500,
            "paid_amount": 750,  # 500 + 250 delivery
            "payment_method": "cash",
            "payment_type": "cash",
            "delivery": {
                "enabled": True,
                "wilaya_code": "16",
                "wilaya_name": "الجزائر",
                "city": "Algiers Center",
                "address": "123 Test Street",
                "delivery_type": "desk",
                "fee": 250
            }
        }
        response = requests.post(f"{BASE_URL}/api/sales", json=sale_data, headers=headers)
        assert response.status_code == 200, f"Sale failed: {response.text}"
        
        sale = response.json()
        assert sale["delivery_fee"] == 250, f"Expected delivery_fee=250, got {sale.get('delivery_fee')}"
        assert sale["total"] == 750, f"Expected total=750, got {sale.get('total')}"
        assert sale["delivery"]["wilaya_code"] == "16"
        assert sale["delivery"]["delivery_type"] == "desk"
        print(f"✓ Sale with delivery: product={500}, delivery={sale['delivery_fee']}, total={sale['total']}")
    
    def test_sale_with_home_delivery(self, auth_token, test_product):
        """Sale with home delivery has higher fee"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        sale_data = {
            "customer_id": None,
            "items": [{
                "product_id": test_product["id"],
                "product_name": test_product["name_en"],
                "quantity": 1,
                "unit_price": 500,
                "discount": 0,
                "total": 500
            }],
            "subtotal": 500,
            "discount": 0,
            "total": 500,
            "paid_amount": 900,
            "payment_method": "cash",
            "payment_type": "cash",
            "delivery": {
                "enabled": True,
                "wilaya_code": "16",
                "wilaya_name": "الجزائر",
                "city": "Algiers Center",
                "address": "456 Home Address",
                "delivery_type": "home",
                "fee": 400  # Home fee is 400 for Algiers
            }
        }
        response = requests.post(f"{BASE_URL}/api/sales", json=sale_data, headers=headers)
        assert response.status_code == 200
        
        sale = response.json()
        assert sale["delivery_fee"] == 400
        assert sale["delivery"]["delivery_type"] == "home"
        print(f"✓ Home delivery sale: delivery_fee={sale['delivery_fee']}")


class TestProductFamilyFilter:
    """Test product filtering by family"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@admin.com",
            "password": "admin"
        })
        return response.json()["access_token"]
    
    def test_get_product_families(self, auth_token):
        """GET /api/product-families - List families"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/product-families", headers=headers)
        assert response.status_code == 200
        
        families = response.json()
        assert isinstance(families, list)
        print(f"✓ Found {len(families)} product families")
    
    def test_filter_products_by_family(self, auth_token):
        """GET /api/products?family_id={id} - Filter by family"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get families
        families_response = requests.get(f"{BASE_URL}/api/product-families", headers=headers)
        families = families_response.json()
        
        if len(families) > 0:
            family_id = families[0]["id"]
            # Filter products by family
            response = requests.get(f"{BASE_URL}/api/products?family_id={family_id}", headers=headers)
            assert response.status_code == 200
            products = response.json()
            print(f"✓ Filtered products by family '{families[0]['name_en']}': {len(products)} products")
        else:
            print("✓ No families found - skipping filter test")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@admin.com",
            "password": "admin"
        })
        return response.json()["access_token"]
    
    def test_cleanup_test_customers(self, auth_token):
        """Delete TEST_ prefixed customers"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        customers = response.json()
        
        deleted = 0
        for c in customers:
            if c["name"].startswith("TEST_"):
                del_response = requests.delete(f"{BASE_URL}/api/customers/{c['id']}", headers=headers)
                if del_response.status_code in [200, 204]:
                    deleted += 1
        print(f"✓ Cleaned up {deleted} test customers")
    
    def test_cleanup_test_products(self, auth_token):
        """Delete TEST_ prefixed products"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products")
        products = response.json()
        
        deleted = 0
        for p in products:
            if p["name_en"].startswith("TEST_"):
                del_response = requests.delete(f"{BASE_URL}/api/products/{p['id']}", headers=headers)
                if del_response.status_code in [200, 204]:
                    deleted += 1
        print(f"✓ Cleaned up {deleted} test products")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
