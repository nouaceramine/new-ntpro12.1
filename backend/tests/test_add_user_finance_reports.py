"""
Test cases for:
1. Add User feature (POST /api/users)
2. Finance Reports in SaaS Admin (GET /api/saas/finance-reports)
3. Payment Methods verification
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Test login with super_admin credentials"""
    
    def test_super_admin_login(self):
        """Test login with super_admin account"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "super_admin"
        assert data["user"]["email"] == "super@ntcommerce.com"
        print(f"PASS: Super admin login successful, role={data['user']['role']}")
        
        # Store token for subsequent tests
        TestAuthentication.token = data["access_token"]

class TestAddUser:
    """Test add user functionality via POST /api/users"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        if not hasattr(TestAuthentication, 'token'):
            # Login to get token
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "super@ntcommerce.com",
                "password": "password"
            })
            if response.status_code == 200:
                TestAuthentication.token = response.json()["access_token"]
            else:
                pytest.skip("Could not authenticate")
        
        self.token = TestAuthentication.token
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_user_success(self):
        """Test creating a new user with valid data"""
        import uuid
        test_email = f"TEST_user_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/users",
            json={
                "name": "Test User",
                "email": test_email,
                "password": "test1234",
                "role": "seller"
            },
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Create user failed: {response.text}"
        data = response.json()
        
        assert data["name"] == "Test User"
        assert data["email"] == test_email
        assert data["role"] == "seller"
        assert "id" in data
        assert "password" not in data  # Password should not be returned
        print(f"PASS: User created successfully with id={data['id']}")
        
        # Verify user exists via GET
        get_response = requests.get(f"{BASE_URL}/api/users", headers=self.headers)
        assert get_response.status_code == 200
        users = get_response.json()
        created_user = next((u for u in users if u["email"] == test_email), None)
        assert created_user is not None, "Created user not found in users list"
        print(f"PASS: User verified in GET /api/users")
        
        # Cleanup - delete test user
        delete_response = requests.delete(
            f"{BASE_URL}/api/users/{data['id']}", 
            headers=self.headers
        )
        assert delete_response.status_code == 200, "Failed to cleanup test user"
        print(f"PASS: Test user cleaned up")
    
    def test_create_user_duplicate_email(self):
        """Test creating user with existing email fails"""
        response = requests.post(
            f"{BASE_URL}/api/users",
            json={
                "name": "Duplicate User",
                "email": "super@ntcommerce.com",  # Existing email
                "password": "test1234",
                "role": "user"
            },
            headers=self.headers
        )
        
        assert response.status_code == 400, f"Expected 400 for duplicate email, got {response.status_code}"
        print(f"PASS: Duplicate email correctly rejected")
    
    def test_create_user_short_password(self):
        """Test creating user with short password fails"""
        import uuid
        response = requests.post(
            f"{BASE_URL}/api/users",
            json={
                "name": "Short Password User",
                "email": f"TEST_short_{uuid.uuid4().hex[:8]}@example.com",
                "password": "123",  # Too short
                "role": "user"
            },
            headers=self.headers
        )
        
        assert response.status_code == 400, f"Expected 400 for short password, got {response.status_code}"
        print(f"PASS: Short password correctly rejected")
    
    def test_create_user_various_roles(self):
        """Test creating users with different roles"""
        import uuid
        roles = ["user", "seller", "manager", "admin", "accountant", "inventory_manager"]
        
        for role in roles:
            test_email = f"TEST_{role}_{uuid.uuid4().hex[:8]}@example.com"
            
            response = requests.post(
                f"{BASE_URL}/api/users",
                json={
                    "name": f"Test {role.capitalize()}",
                    "email": test_email,
                    "password": "test1234",
                    "role": role
                },
                headers=self.headers
            )
            
            assert response.status_code == 200, f"Create user with role {role} failed: {response.text}"
            data = response.json()
            assert data["role"] == role
            print(f"PASS: User created with role={role}")
            
            # Cleanup
            requests.delete(f"{BASE_URL}/api/users/{data['id']}", headers=self.headers)
    
    def test_create_user_without_auth(self):
        """Test creating user without authentication fails"""
        import uuid
        response = requests.post(
            f"{BASE_URL}/api/users",
            json={
                "name": "Unauth User",
                "email": f"TEST_unauth_{uuid.uuid4().hex[:8]}@example.com",
                "password": "test1234",
                "role": "user"
            }
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"PASS: Unauthenticated request correctly rejected")


class TestFinanceReports:
    """Test finance reports functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        if not hasattr(TestAuthentication, 'token'):
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "super@ntcommerce.com",
                "password": "password"
            })
            if response.status_code == 200:
                TestAuthentication.token = response.json()["access_token"]
            else:
                pytest.skip("Could not authenticate")
        
        self.token = TestAuthentication.token
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_finance_reports_all(self):
        """Test getting finance reports with 'all' range"""
        response = requests.get(
            f"{BASE_URL}/api/saas/finance-reports?range=all",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Finance reports failed: {response.text}"
        data = response.json()
        
        # Verify required fields exist
        assert "total_revenue" in data
        assert "monthly_revenue" in data
        assert "yearly_revenue" in data
        assert "expenses" in data
        assert "net_profit" in data
        assert "pending_payments" in data
        assert "payment_methods" in data
        
        print(f"PASS: Finance reports returned successfully")
        print(f"  - Total Revenue: {data['total_revenue']}")
        print(f"  - Monthly Revenue: {data['monthly_revenue']}")
        print(f"  - Yearly Revenue: {data['yearly_revenue']}")
        print(f"  - Net Profit: {data['net_profit']}")
    
    def test_get_finance_reports_monthly(self):
        """Test getting finance reports with 'month' range"""
        response = requests.get(
            f"{BASE_URL}/api/saas/finance-reports?range=month",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Finance reports (month) failed: {response.text}"
        data = response.json()
        
        assert "total_revenue" in data
        assert "monthly_revenue" in data
        print(f"PASS: Monthly finance reports returned")
    
    def test_get_finance_reports_yearly(self):
        """Test getting finance reports with 'year' range"""
        response = requests.get(
            f"{BASE_URL}/api/saas/finance-reports?range=year",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Finance reports (year) failed: {response.text}"
        data = response.json()
        
        assert "total_revenue" in data
        assert "yearly_revenue" in data
        print(f"PASS: Yearly finance reports returned")
    
    def test_payment_methods_structure(self):
        """Test payment methods structure in finance reports"""
        response = requests.get(
            f"{BASE_URL}/api/saas/finance-reports?range=all",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        payment_methods = data.get("payment_methods", {})
        
        # Verify all payment methods exist
        expected_methods = ["cash", "ccp", "bank_transfer", "stripe", "manual"]
        for method in expected_methods:
            assert method in payment_methods, f"Payment method '{method}' missing"
            assert "count" in payment_methods[method]
            assert "amount" in payment_methods[method]
        
        print(f"PASS: Payment methods structure verified")
        print(f"  - CCP: {payment_methods.get('ccp', {})}")
        print(f"  - Bank Transfer: {payment_methods.get('bank_transfer', {})}")
        print(f"  - Stripe: {payment_methods.get('stripe', {})}")
        print(f"  - Cash: {payment_methods.get('cash', {})}")
        print(f"  - Manual: {payment_methods.get('manual', {})}")
    
    def test_net_profit_calculation(self):
        """Test that net profit is calculated correctly (revenue - expenses)"""
        response = requests.get(
            f"{BASE_URL}/api/saas/finance-reports?range=all",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        total_revenue = data["total_revenue"]
        expenses = data["expenses"]
        net_profit = data["net_profit"]
        
        # Verify net_profit = total_revenue - expenses
        expected_profit = total_revenue - expenses
        assert abs(net_profit - expected_profit) < 0.01, f"Net profit calculation error: {net_profit} != {expected_profit}"
        
        # Verify expenses are 30% of revenue (as per backend logic)
        expected_expenses = total_revenue * 0.3
        assert abs(expenses - expected_expenses) < 0.01, f"Expenses calculation error: {expenses} != {expected_expenses}"
        
        print(f"PASS: Net profit calculation verified")
        print(f"  - Revenue: {total_revenue}, Expenses (30%): {expenses}, Net Profit: {net_profit}")
    
    def test_finance_reports_without_super_admin(self):
        """Test that finance reports require super_admin role"""
        # First, try to get a regular admin or user token
        # Create a test user
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "super@ntcommerce.com",
            "password": "password"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        import uuid
        test_email = f"TEST_finance_check_{uuid.uuid4().hex[:8]}@example.com"
        
        create_resp = requests.post(
            f"{BASE_URL}/api/users",
            json={
                "name": "Test Regular",
                "email": test_email,
                "password": "test1234",
                "role": "admin"  # Regular admin, not super_admin
            },
            headers=headers
        )
        
        if create_resp.status_code == 200:
            user_id = create_resp.json()["id"]
            
            # Login as regular admin
            login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": test_email,
                "password": "test1234"
            })
            
            if login_resp.status_code == 200:
                regular_token = login_resp.json()["access_token"]
                regular_headers = {"Authorization": f"Bearer {regular_token}"}
                
                # Try to access finance reports
                finance_resp = requests.get(
                    f"{BASE_URL}/api/saas/finance-reports?range=all",
                    headers=regular_headers
                )
                
                # Should get 403
                assert finance_resp.status_code == 403, f"Expected 403 for non-super_admin, got {finance_resp.status_code}"
                print(f"PASS: Finance reports correctly restricted to super_admin")
            
            # Cleanup
            requests.delete(f"{BASE_URL}/api/users/{user_id}", headers=headers)
        else:
            print(f"SKIP: Could not create test user for authorization check")


class TestSaasPages:
    """Test SaaS admin page related APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        if not hasattr(TestAuthentication, 'token'):
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "super@ntcommerce.com",
                "password": "password"
            })
            if response.status_code == 200:
                TestAuthentication.token = response.json()["access_token"]
            else:
                pytest.skip("Could not authenticate")
        
        self.token = TestAuthentication.token
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_saas_stats(self):
        """Test GET /api/saas/stats"""
        response = requests.get(f"{BASE_URL}/api/saas/stats", headers=self.headers)
        
        assert response.status_code == 200, f"SaaS stats failed: {response.text}"
        data = response.json()
        
        assert "total_tenants" in data
        assert "active_tenants" in data
        assert "trial_tenants" in data
        print(f"PASS: SaaS stats returned - {data.get('total_tenants', 0)} tenants")
    
    def test_get_saas_tenants(self):
        """Test GET /api/saas/tenants"""
        response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=self.headers)
        
        assert response.status_code == 200, f"SaaS tenants failed: {response.text}"
        print(f"PASS: SaaS tenants list returned")
    
    def test_get_saas_payments(self):
        """Test GET /api/saas/payments"""
        response = requests.get(f"{BASE_URL}/api/saas/payments", headers=self.headers)
        
        assert response.status_code == 200, f"SaaS payments failed: {response.text}"
        print(f"PASS: SaaS payments list returned")
    
    def test_get_saas_plans(self):
        """Test GET /api/saas/plans"""
        response = requests.get(f"{BASE_URL}/api/saas/plans?include_inactive=true", headers=self.headers)
        
        assert response.status_code == 200, f"SaaS plans failed: {response.text}"
        print(f"PASS: SaaS plans list returned")


class TestUsersPage:
    """Test users page related APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        if not hasattr(TestAuthentication, 'token'):
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "super@ntcommerce.com",
                "password": "password"
            })
            if response.status_code == 200:
                TestAuthentication.token = response.json()["access_token"]
            else:
                pytest.skip("Could not authenticate")
        
        self.token = TestAuthentication.token
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_users_list(self):
        """Test GET /api/users returns list of users"""
        response = requests.get(f"{BASE_URL}/api/users", headers=self.headers)
        
        assert response.status_code == 200, f"Get users failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        
        # Verify super admin exists in list
        super_admin = next((u for u in data if u["email"] == "super@ntcommerce.com"), None)
        assert super_admin is not None, "Super admin not found in users list"
        assert super_admin["role"] == "super_admin"
        
        print(f"PASS: Users list returned with {len(data)} users")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
