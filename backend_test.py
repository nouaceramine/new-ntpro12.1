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
        """Test product creation (admin only)"""
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
                "quantity": 50,
                "image_url": "https://example.com/test-image.jpg",
                "compatible_models": ["iPhone 15 Pro", "iPhone 15 Pro Max", "Samsung Galaxy S24"]
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
        """Test product search functionality"""
        success1, _ = self.run_test(
            "Search Products by Name",
            "GET",
            "products?search=Test",
            200
        )
        success2, _ = self.run_test(
            "Search Products by Model",
            "GET",
            "products?model=iPhone",
            200
        )
        return success1 and success2

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
    # Authentication tests
    admin_reg_ok = tester.test_admin_registration()
    user_reg_ok = tester.test_user_registration() 
    get_user_ok = tester.test_get_current_user()
    
    print("\n=== PRODUCT CRUD TESTS ===")
    # Product CRUD tests
    create_ok = tester.test_create_product()
    get_all_ok = tester.test_get_products()
    search_ok = tester.test_search_products()
    get_single_ok = tester.test_get_single_product()
    update_ok = tester.test_update_product()
    
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