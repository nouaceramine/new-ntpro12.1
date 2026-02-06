import requests
import sys
from datetime import datetime
import json

class ScreenGuardPOSAPITester:
    def __init__(self, base_url="https://inventory-sales-hub-4.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.customer_id = None
        self.supplier_id = None
        self.product_id = None
        self.sale_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.text else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_response = response.json()
                    print(f"   Error response: {error_response}")
                except:
                    print(f"   Error text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test login with existing admin credentials"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": "admin@screenguard.com",
                "password": "Admin123!"
            }
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
        return success

    def test_create_sample_product(self):
        """Create a sample product for sales testing"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        success, response = self.run_test(
            "Create Sample Product",
            "POST",
            "products",
            200,
            data={
                "name_en": "iPhone 15 Pro Screen Guard",
                "name_ar": "واقي شاشة آيفون 15 برو",
                "description_en": "Premium tempered glass screen protector",
                "description_ar": "واقي شاشة زجاجي ممتاز",
                "purchase_price": 15.00,
                "wholesale_price": 25.00,
                "retail_price": 35.00,
                "quantity": 100,
                "image_url": "https://example.com/screen-guard.jpg",
                "compatible_models": ["iPhone 15 Pro", "iPhone 15 Pro Max"],
                "low_stock_threshold": 10,
                "barcode": "123456789"
            },
            token=self.admin_token
        )
        if success and 'id' in response:
            self.product_id = response['id']
            print(f"   Product created with ID: {self.product_id}")
        return success

    def test_create_customer(self):
        """Test customer creation"""
        success, response = self.run_test(
            "Create Customer",
            "POST",
            "customers",
            200,
            data={
                "name": "Ahmed Hassan",
                "phone": "+213555123456",
                "email": "ahmed@example.com",
                "address": "123 Algiers Street, Algiers",
                "notes": "VIP customer"
            },
            token=self.admin_token
        )
        if success and 'id' in response:
            self.customer_id = response['id']
            print(f"   Customer created with ID: {self.customer_id}")
        return success

    def test_list_customers(self):
        """Test listing customers"""
        success, response = self.run_test(
            "List Customers",
            "GET",
            "customers",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Found {len(response)} customers")
        return success

    def test_create_supplier(self):
        """Test supplier creation"""
        success, response = self.run_test(
            "Create Supplier",
            "POST",
            "suppliers",
            200,
            data={
                "name": "Glass Pro Supplier",
                "phone": "+213666789012",
                "email": "supplier@glasspro.dz",
                "address": "Industrial Zone, Oran",
                "notes": "Main supplier for premium glass"
            },
            token=self.admin_token
        )
        if success and 'id' in response:
            self.supplier_id = response['id']
            print(f"   Supplier created with ID: {self.supplier_id}")
        return success

    def test_list_suppliers(self):
        """Test listing suppliers"""
        success, response = self.run_test(
            "List Suppliers",
            "GET",
            "suppliers",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Found {len(response)} suppliers")
        return success

    def test_get_cash_boxes(self):
        """Test getting cash boxes"""
        success, response = self.run_test(
            "Get Cash Boxes",
            "GET",
            "cash-boxes",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Found {len(response)} cash boxes")
            for box in response:
                print(f"     {box['name']}: {box['balance']} دج")
        return success

    def test_create_sale(self):
        """Test creating a sale with multiple payment methods"""
        if not self.customer_id or not self.product_id:
            print("❌ Skipping - Need customer and product IDs")
            return False
            
        success, response = self.run_test(
            "Create Sale",
            "POST",
            "sales",
            200,
            data={
                "customer_id": self.customer_id,
                "items": [
                    {
                        "product_id": self.product_id,
                        "product_name": "iPhone 15 Pro Screen Guard",
                        "quantity": 2,
                        "unit_price": 35.00,
                        "discount": 5.00,
                        "total": 65.00
                    }
                ],
                "subtotal": 70.00,
                "discount": 5.00,
                "total": 65.00,
                "paid_amount": 65.00,
                "payment_method": "cash",
                "notes": "Test sale"
            },
            token=self.admin_token
        )
        if success and 'id' in response:
            self.sale_id = response['id']
            print(f"   Sale created with ID: {self.sale_id}")
            print(f"   Invoice: {response.get('invoice_number')}")
        return success

    def test_list_sales(self):
        """Test listing sales"""
        success, response = self.run_test(
            "List Sales",
            "GET",
            "sales",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Found {len(response)} sales")
        return success

    def test_return_sale(self):
        """Test returning a sale"""
        if not self.sale_id:
            print("❌ Skipping - Need sale ID")
            return False
            
        success, response = self.run_test(
            "Return Sale",
            "POST",
            f"sales/{self.sale_id}/return",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Sale returned successfully")
        return success

    def test_cash_transfer(self):
        """Test transferring money between cash boxes"""
        # Transfer from bank to cash (bank has money from previous sales)
        success, response = self.run_test(
            "Transfer Between Cash Boxes",
            "POST",
            "cash-boxes/transfer?from_box=bank&to_box=cash&amount=10.0",
            200,
            token=self.admin_token
        )
        return success

    def test_get_transactions(self):
        """Test getting transaction history"""
        success, response = self.run_test(
            "Get Transactions",
            "GET",
            "transactions",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Found {len(response)} transactions")
        return success

    def test_get_stats_with_cash_boxes(self):
        """Test getting dashboard stats including cash boxes"""
        success, response = self.run_test(
            "Get Dashboard Stats",
            "GET",
            "stats",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Stats: Products: {response.get('total_products')}, "
                  f"Customers: {response.get('total_customers')}, "
                  f"Total Cash: {response.get('total_cash')} دج")
        return success

    def test_create_bank_payment_sale(self):
        """Test creating a sale with bank payment"""
        if not self.customer_id or not self.product_id:
            print("❌ Skipping - Need customer and product IDs")
            return False
            
        success, response = self.run_test(
            "Create Sale (Bank Payment)",
            "POST",
            "sales",
            200,
            data={
                "customer_id": self.customer_id,
                "items": [
                    {
                        "product_id": self.product_id,
                        "product_name": "iPhone 15 Pro Screen Guard",
                        "quantity": 1,
                        "unit_price": 35.00,
                        "discount": 0.00,
                        "total": 35.00
                    }
                ],
                "subtotal": 35.00,
                "discount": 0.00,
                "total": 35.00,
                "paid_amount": 35.00,
                "payment_method": "bank",
                "notes": "Bank payment test"
            },
            token=self.admin_token
        )
        return success

    def test_create_wallet_payment_sale(self):
        """Test creating a sale with wallet payment"""
        if not self.customer_id or not self.product_id:
            print("❌ Skipping - Need customer and product IDs")
            return False
            
        success, response = self.run_test(
            "Create Sale (Wallet Payment)",
            "POST",
            "sales",
            200,
            data={
                "customer_id": self.customer_id,
                "items": [
                    {
                        "product_id": self.product_id,
                        "product_name": "iPhone 15 Pro Screen Guard",
                        "quantity": 1,
                        "unit_price": 35.00,
                        "discount": 0.00,
                        "total": 35.00
                    }
                ],
                "subtotal": 35.00,
                "discount": 0.00,
                "total": 35.00,
                "paid_amount": 35.00,
                "payment_method": "wallet",
                "notes": "Wallet payment test"
            },
            token=self.admin_token
        )
        return success

def main():
    print("🧪 Starting ScreenGuard POS API Testing...")
    print("=" * 60)
    
    tester = ScreenGuardPOSAPITester()
    
    # Test sequence
    print("\n=== AUTHENTICATION ===")
    auth_ok = tester.test_admin_login()
    if not auth_ok:
        print("❌ Authentication failed - cannot continue")
        return 1

    print("\n=== PRODUCT SETUP ===")
    product_ok = tester.test_create_sample_product()

    print("\n=== CUSTOMER MANAGEMENT ===")
    create_customer_ok = tester.test_create_customer()
    list_customers_ok = tester.test_list_customers()

    print("\n=== SUPPLIER MANAGEMENT ===")
    create_supplier_ok = tester.test_create_supplier()
    list_suppliers_ok = tester.test_list_suppliers()

    print("\n=== CASH BOX MANAGEMENT ===")
    cash_boxes_ok = tester.test_get_cash_boxes()
    transactions_ok = tester.test_get_transactions()

    print("\n=== SALES MANAGEMENT ===")
    create_sale_ok = tester.test_create_sale()
    list_sales_ok = tester.test_list_sales()
    
    # Test different payment methods
    bank_sale_ok = tester.test_create_bank_payment_sale()
    wallet_sale_ok = tester.test_create_wallet_payment_sale()
    
    return_sale_ok = tester.test_return_sale()

    print("\n=== CASH TRANSFERS ===")
    transfer_ok = tester.test_cash_transfer()

    print("\n=== DASHBOARD STATS ===")
    stats_ok = tester.test_get_stats_with_cash_boxes()

    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 TESTING SUMMARY")
    print(f"   Tests run: {tester.tests_run}")
    print(f"   Tests passed: {tester.tests_passed}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All POS tests PASSED!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())