import requests
import sys
from datetime import datetime
import json

class MobileGlassAPITester:
    def __init__(self, base_url="https://mobile-glass-search.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.admin_token = None
        self.user_token = None
        self.admin_user_id = None
        self.regular_user_id = None
        self.test_product_id = None
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

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n=== HEALTH CHECK TESTS ===")
        success1, _ = self.run_test("API Root", "GET", "", 200)
        success2, _ = self.run_test("Health Check", "GET", "health", 200)
        return success1 and success2

    def test_admin_registration(self):
        """Test admin user registration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        success, response = self.run_test(
            "Admin Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": f"admin_test_{timestamp}@test.com",
                "password": "AdminTest123!",
                "name": f"Admin User {timestamp}",
                "role": "admin"
            }
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user_id = response['user']['id']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
        return success

    def test_user_registration(self):
        """Test regular user registration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register", 
            200,
            data={
                "email": f"user_test_{timestamp}@test.com",
                "password": "UserTest123!",
                "name": f"Regular User {timestamp}",
                "role": "user"
            }
        )
        if success and 'access_token' in response:
            self.user_token = response['access_token']
            self.regular_user_id = response['user']['id']
            print(f"   User token obtained: {self.user_token[:20]}...")
        return success

    def test_login(self):
        """Test login functionality"""
        # Test with the admin user
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": f"admin_test_{timestamp}@test.com",
                "password": "AdminTest123!"
            }
        )
        return success

    def test_get_current_user(self):
        """Test get current user endpoint"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        success, response = self.run_test(
            "Get Current User",
            "GET", 
            "auth/me",
            200,
            token=self.admin_token
        )
        return success

    def test_create_product(self):
        """Test product creation (admin only) with low stock threshold"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        success, response = self.run_test(
            "Create Product",
            "POST",
            "products",
            200,
            data={
                "name_en": "Test Screen Protector",
                "name_ar": "واقي شاشة تجريبي",
                "description_en": "High-quality tempered glass screen protector for testing",
                "description_ar": "واقي شاشة زجاجي عالي الجودة للاختبار",
                "price": 25.99,
                "quantity": 5,  # Low quantity to test alerts
                "image_url": "https://example.com/test-image.jpg",
                "compatible_models": ["iPhone 15 Pro", "iPhone 15 Pro Max", "Samsung Galaxy S24"],
                "low_stock_threshold": 10
            },
            token=self.admin_token
        )
        if success and 'id' in response:
            self.test_product_id = response['id']
            print(f"   Product created with ID: {self.test_product_id}")
        return success

    def test_get_products(self):
        """Test getting all products"""
        success, response = self.run_test(
            "Get All Products",
            "GET",
            "products",
            200
        )
        if success:
            print(f"   Found {len(response)} products")
        return success

    def test_search_products(self):
        """Test product search functionality including compatible models"""
        # Search by name
        success1, response1 = self.run_test(
            "Search Products by Name",
            "GET",
            "products?search=Test",
            200
        )
        
        # Search by compatible model (new feature)
        success2, response2 = self.run_test(
            "Search Products by Compatible Model",
            "GET", 
            "products?search=iPhone",
            200
        )
        
        # Test specific model search
        success3, response3 = self.run_test(
            "Search Products with Model Parameter",
            "GET",
            "products?model=Galaxy",
            200
        )
        
        if success1:
            print(f"   Found {len(response1)} products by name")
        if success2:
            print(f"   Found {len(response2)} products by compatible model")
        if success3:
            print(f"   Found {len(response3)} products with model parameter")
            
        return success1 and success2 and success3

    def test_get_single_product(self):
        """Test getting a single product"""
        if not self.test_product_id:
            print("❌ Skipping - No test product ID available")
            return False
            
        success, _ = self.run_test(
            "Get Single Product",
            "GET",
            f"products/{self.test_product_id}",
            200
        )
        return success

    def test_update_product(self):
        """Test updating a product (admin only)"""
        if not self.admin_token or not self.test_product_id:
            print("❌ Skipping - No admin token or product ID available")
            return False
            
        success, _ = self.run_test(
            "Update Product",
            "PUT",
            f"products/{self.test_product_id}",
            200,
            data={
                "price": 29.99,
                "quantity": 45,
                "name_en": "Updated Test Screen Protector"
            },
            token=self.admin_token
        )
        return success

    def test_delete_product(self):
        """Test deleting a product (admin only)"""
        if not self.admin_token or not self.test_product_id:
            print("❌ Skipping - No admin token or product ID available")
            return False
            
        success, _ = self.run_test(
            "Delete Product",
            "DELETE",
            f"products/{self.test_product_id}",
            200,
            token=self.admin_token
        )
        return success

    def test_get_stats(self):
        """Test getting statistics (admin only)"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        success, response = self.run_test(
            "Get Stats",
            "GET",
            "stats",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Stats: {response}")
        return success

    def test_unauthorized_access(self):
        """Test unauthorized access scenarios"""
        print("\n=== AUTHORIZATION TESTS ===")
        
        # Test creating product without token
        success1, _ = self.run_test(
            "Create Product (No Token)",
            "POST",
            "products",
            401,  # Expecting unauthorized
            data={
                "name_en": "Unauthorized Test",
                "name_ar": "اختبار غير مصرح",
                "price": 10.0,
                "quantity": 1,
                "compatible_models": ["Test Model"]
            }
        )
        
        # Test creating product with regular user token
        if self.user_token:
            success2, _ = self.run_test(
                "Create Product (User Token)",
                "POST", 
                "products",
                403,  # Expecting forbidden
                data={
                    "name_en": "User Test",
                    "name_ar": "اختبار مستخدم", 
                    "price": 10.0,
                    "quantity": 1,
                    "compatible_models": ["Test Model"]
                },
                token=self.user_token
            )
        else:
            success2 = True  # Skip if no user token
            print("   Skipping user token test - no user token available")
        
        return success1 and success2

    def test_user_management(self):
        """Test user management endpoints (admin only)"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        print("\n=== USER MANAGEMENT TESTS ===")
        
        # Test get all users
        success1, response1 = self.run_test(
            "Get All Users (Admin)",
            "GET",
            "users",
            200,
            token=self.admin_token
        )
        if success1:
            print(f"   Found {len(response1)} users")
        
        # Test get specific user
        if self.regular_user_id:
            success2, response2 = self.run_test(
                "Get Specific User",
                "GET",
                f"users/{self.regular_user_id}",
                200,
                token=self.admin_token
            )
        else:
            success2 = True
            print("   Skipping get specific user - no regular user ID")
        
        # Test update user role
        if self.regular_user_id:
            success3, response3 = self.run_test(
                "Update User Role",
                "PUT",
                f"users/{self.regular_user_id}",
                200,
                data={"role": "admin"},
                token=self.admin_token
            )
            
            # Change back to user role
            success3b, response3b = self.run_test(
                "Change Back to User Role",
                "PUT",
                f"users/{self.regular_user_id}",
                200,
                data={"role": "user"},
                token=self.admin_token
            )
            success3 = success3 and success3b
        else:
            success3 = True
            print("   Skipping update user role - no regular user ID")
        
        # Test unauthorized access to user endpoints
        success4, _ = self.run_test(
            "Get Users (No Token)",
            "GET",
            "users",
            401
        )
        
        if self.user_token:
            success5, _ = self.run_test(
                "Get Users (Regular User)",
                "GET",
                "users",
                403,
                token=self.user_token
            )
        else:
            success5 = True
            print("   Skipping regular user test - no user token")
        
        return success1 and success2 and success3 and success4 and success5

    def test_low_stock_alerts(self):
        """Test low stock alert functionality"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        print("\n=== LOW STOCK ALERT TESTS ===")
        
        # Test get low stock products
        success1, response1 = self.run_test(
            "Get Low Stock Products",
            "GET",
            "products/alerts/low-stock",
            200,
            token=self.admin_token
        )
        
        if success1:
            print(f"   Found {len(response1)} low stock products")
            # Since we created a product with quantity=5 and threshold=10, it should appear
            if len(response1) > 0:
                print(f"   Low stock products detected correctly")
            else:
                print("   Warning: Expected at least one low stock product")
        
        # Test unauthorized access
        success2, _ = self.run_test(
            "Get Low Stock (No Token)",
            "GET", 
            "products/alerts/low-stock",
            401
        )
        
        if self.user_token:
            success3, _ = self.run_test(
                "Get Low Stock (Regular User)",
                "GET",
                "products/alerts/low-stock", 
                403,
                token=self.user_token
            )
        else:
            success3 = True
            print("   Skipping regular user test - no user token")
        
        return success1 and success2 and success3

    def test_ocr_endpoint(self):
        """Test OCR model extraction endpoint"""
        if not self.admin_token:
            print("❌ Skipping - No admin token available")
            return False
            
        print("\n=== OCR ENDPOINT TESTS ===")
        
        # Create a simple test base64 image (1x1 transparent PNG)
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQIHWPIyMgAAAABAAEAACsRrAEAAAAASUVORK5CYII="
        
        success1, response1 = self.run_test(
            "OCR Extract Models",
            "POST",
            "ocr/extract-models",
            200,
            data={"image_base64": test_image_base64},
            token=self.admin_token
        )
        
        if success1:
            print(f"   OCR Response: {response1}")
        
        # Test unauthorized access
        success2, _ = self.run_test(
            "OCR Extract (No Token)",
            "POST",
            "ocr/extract-models",
            401,
            data={"image_base64": test_image_base64}
        )
        
        if self.user_token:
            success3, _ = self.run_test(
                "OCR Extract (Regular User)",
                "POST",
                "ocr/extract-models",
                403,
                data={"image_base64": test_image_base64},
                token=self.user_token
            )
        else:
            success3 = True
            print("   Skipping regular user test - no user token")
        
        return success1 and success2 and success3

    def test_existing_admin_login(self):
        """Test login with existing admin credentials"""
        success, response = self.run_test(
            "Existing Admin Login",
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
            self.admin_user_id = response['user']['id']
            print(f"   Existing admin token obtained: {self.admin_token[:20]}...")
        return success

def main():
    print("🧪 Starting Mobile Glass Search API Testing...")
    print("=" * 60)
    
    tester = MobileGlassAPITester()
    
    # Health check
    health_ok = tester.test_health_check()
    if not health_ok:
        print("\n❌ Health check failed - API might be down")
        return 1
    
    print("\n=== AUTHENTICATION TESTS ===")
    # Try existing admin first, then create new if needed
    existing_admin_ok = tester.test_existing_admin_login()
    if not existing_admin_ok:
        admin_reg_ok = tester.test_admin_registration()
    else:
        admin_reg_ok = True
        
    user_reg_ok = tester.test_user_registration() 
    get_user_ok = tester.test_get_current_user()
    
    # New user management tests
    user_mgmt_ok = tester.test_user_management()
    
    print("\n=== PRODUCT CRUD TESTS ===")
    # Product CRUD tests
    create_ok = tester.test_create_product()
    get_all_ok = tester.test_get_products()
    search_ok = tester.test_search_products()
    get_single_ok = tester.test_get_single_product()
    update_ok = tester.test_update_product()
    
    # New low stock alert tests
    low_stock_ok = tester.test_low_stock_alerts()
    
    # OCR tests
    ocr_ok = tester.test_ocr_endpoint()
    
    print("\n=== ADMIN TESTS ===")
    # Admin-specific tests
    stats_ok = tester.test_get_stats()
    
    # Authorization tests
    auth_ok = tester.test_unauthorized_access()
    
    # Cleanup - delete test product
    delete_ok = tester.test_delete_product()
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 TESTING SUMMARY")
    print(f"   Tests run: {tester.tests_run}")
    print(f"   Tests passed: {tester.tests_passed}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests PASSED!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())