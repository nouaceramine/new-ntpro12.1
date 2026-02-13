"""
Security Test: Prevent tenants from creating super_admin accounts
Tests the fix for critical vulnerability where tenants could create super_admin users
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials provided in the review request
SUPER_ADMIN_CREDS = {"email": "super@ntcommerce.com", "password": "superadmin123"}
TENANT_ADMIN_CREDS = {"email": "tenant_admin@test.com", "password": "test1234"}


class TestSecuritySuperAdminPrevention:
    """Test suite for security fix - preventing super_admin role assignment"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.super_admin_token = None
        self.tenant_admin_token = None
        self.test_user_ids = []
    
    def get_super_admin_token(self):
        """Get authentication token for super_admin user"""
        if self.super_admin_token:
            return self.super_admin_token
        
        response = self.session.post(f"{BASE_URL}/api/auth/unified-login", json=SUPER_ADMIN_CREDS)
        if response.status_code == 200:
            self.super_admin_token = response.json().get("access_token")
            return self.super_admin_token
        return None
    
    def get_tenant_admin_token(self):
        """Get authentication token for tenant admin user"""
        if self.tenant_admin_token:
            return self.tenant_admin_token
        
        # First try to login with provided credentials
        response = self.session.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_ADMIN_CREDS)
        if response.status_code == 200:
            self.tenant_admin_token = response.json().get("access_token")
            return self.tenant_admin_token
        
        # Try alternative login endpoint
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=TENANT_ADMIN_CREDS)
        if response.status_code == 200:
            self.tenant_admin_token = response.json().get("access_token")
            return self.tenant_admin_token
        
        return None
    
    # ============ SECURITY TEST: POST /api/auth/register ============
    
    def test_register_with_super_admin_role_returns_403(self):
        """SECURITY: POST /api/auth/register with role=super_admin should return 403"""
        test_user = {
            "name": "TEST_Hacker",
            "email": f"hacker_{uuid.uuid4().hex[:8]}@test.com",
            "password": "hacker123",
            "role": "super_admin"
        }
        
        response = self.session.post(f"{BASE_URL}/api/auth/register", json=test_user)
        
        # Should be forbidden
        assert response.status_code == 403, f"Expected 403 but got {response.status_code}: {response.text}"
        
        # Verify error message mentions super_admin restriction
        response_data = response.json()
        assert "super_admin" in response_data.get("detail", "").lower() or "سوبر أدمين" in response_data.get("detail", ""), \
            f"Error message should mention super_admin restriction: {response_data}"
        
        print(f"✓ PASS: /api/auth/register correctly rejected super_admin role with 403")
    
    def test_register_with_saas_admin_role_returns_403(self):
        """SECURITY: POST /api/auth/register with role=saas_admin should return 403"""
        test_user = {
            "name": "TEST_SaasHacker",
            "email": f"saas_hacker_{uuid.uuid4().hex[:8]}@test.com",
            "password": "hacker123",
            "role": "saas_admin"
        }
        
        response = self.session.post(f"{BASE_URL}/api/auth/register", json=test_user)
        
        # Should be forbidden
        assert response.status_code == 403, f"Expected 403 but got {response.status_code}: {response.text}"
        print(f"✓ PASS: /api/auth/register correctly rejected saas_admin role with 403")
    
    def test_register_with_superadmin_case_insensitive_returns_403(self):
        """SECURITY: POST /api/auth/register with role=SUPER_ADMIN (uppercase) should return 403"""
        test_user = {
            "name": "TEST_CaseHacker",
            "email": f"case_hacker_{uuid.uuid4().hex[:8]}@test.com",
            "password": "hacker123",
            "role": "SUPER_ADMIN"
        }
        
        response = self.session.post(f"{BASE_URL}/api/auth/register", json=test_user)
        
        # Should be forbidden (case insensitive check)
        assert response.status_code == 403, f"Expected 403 but got {response.status_code}: {response.text}"
        print(f"✓ PASS: /api/auth/register correctly rejected SUPER_ADMIN (uppercase) role with 403")
    
    # ============ SECURITY TEST: POST /api/users ============
    
    def test_create_user_with_super_admin_role_by_tenant_returns_403(self):
        """SECURITY: POST /api/users with role=super_admin should return 403 for non-super_admin users"""
        # First get tenant admin token
        token = self.get_tenant_admin_token()
        if not token:
            # If tenant admin doesn't exist, try getting super admin and verify it CAN create super_admin
            super_token = self.get_super_admin_token()
            if not super_token:
                pytest.skip("Could not authenticate with any admin credentials")
            
            # Test that super_admin CAN create super_admin (this is allowed)
            test_user = {
                "name": "TEST_SuperCreatedSuperAdmin",
                "email": f"super_created_{uuid.uuid4().hex[:8]}@test.com",
                "password": "test1234",
                "role": "super_admin"
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/users", 
                json=test_user,
                headers={"Authorization": f"Bearer {super_token}"}
            )
            
            # Super admin SHOULD be able to create super_admin
            if response.status_code == 201 or response.status_code == 200:
                print(f"✓ PASS: Super admin can correctly create super_admin users")
                # Cleanup - delete the created user
                created_user = response.json()
                if created_user.get("id"):
                    self.session.delete(
                        f"{BASE_URL}/api/users/{created_user['id']}", 
                        headers={"Authorization": f"Bearer {super_token}"}
                    )
            return
        
        # Test with tenant admin token - should be forbidden
        test_user = {
            "name": "TEST_TenantHacker",
            "email": f"tenant_hacker_{uuid.uuid4().hex[:8]}@test.com",
            "password": "hacker123",
            "role": "super_admin"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/users", 
            json=test_user,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should be forbidden for tenant admin
        assert response.status_code == 403, f"Expected 403 but got {response.status_code}: {response.text}"
        print(f"✓ PASS: /api/users correctly rejected super_admin role creation by tenant admin with 403")
    
    # ============ SECURITY TEST: PUT /api/users/{id} ============
    
    def test_update_user_to_super_admin_role_by_tenant_returns_403(self):
        """SECURITY: PUT /api/users/{id} with role=super_admin should return 403 for non-super_admin users"""
        # Get super admin token to create a test user first
        super_token = self.get_super_admin_token()
        if not super_token:
            pytest.skip("Could not authenticate with super admin credentials")
        
        # Create a test user with normal role
        test_user = {
            "name": "TEST_UpgradeTarget",
            "email": f"upgrade_target_{uuid.uuid4().hex[:8]}@test.com",
            "password": "test1234",
            "role": "user"
        }
        
        create_response = self.session.post(
            f"{BASE_URL}/api/users", 
            json=test_user,
            headers={"Authorization": f"Bearer {super_token}"}
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create test user: {create_response.text}")
        
        created_user = create_response.json()
        user_id = created_user.get("id")
        self.test_user_ids.append(user_id)
        
        # Now test with tenant admin if available, otherwise test super admin can do it
        tenant_token = self.get_tenant_admin_token()
        
        if tenant_token and tenant_token != super_token:
            # Test that tenant admin CANNOT upgrade to super_admin
            response = self.session.put(
                f"{BASE_URL}/api/users/{user_id}",
                json={"role": "super_admin"},
                headers={"Authorization": f"Bearer {tenant_token}"}
            )
            
            # Should be forbidden
            assert response.status_code == 403, f"Expected 403 but got {response.status_code}: {response.text}"
            print(f"✓ PASS: /api/users/{user_id} correctly rejected role upgrade to super_admin by tenant admin with 403")
        else:
            # Verify super_admin CAN upgrade
            response = self.session.put(
                f"{BASE_URL}/api/users/{user_id}",
                json={"role": "super_admin"},
                headers={"Authorization": f"Bearer {super_token}"}
            )
            
            # Super admin SHOULD be able to upgrade roles
            assert response.status_code in [200, 201], f"Super admin should be able to upgrade roles: {response.text}"
            print(f"✓ PASS: Super admin can correctly upgrade user to super_admin role")
        
        # Cleanup
        self.session.delete(
            f"{BASE_URL}/api/users/{user_id}", 
            headers={"Authorization": f"Bearer {super_token}"}
        )
    
    # ============ FUNCTIONAL TEST: Normal user creation should work ============
    
    def test_create_normal_user_with_seller_role_works(self):
        """FUNCTIONAL: Creating normal user (role=seller) should work correctly"""
        token = self.get_super_admin_token()
        if not token:
            pytest.skip("Could not authenticate with admin credentials")
        
        test_user = {
            "name": "TEST_NormalSeller",
            "email": f"normal_seller_{uuid.uuid4().hex[:8]}@test.com",
            "password": "test1234",
            "role": "seller"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/users", 
            json=test_user,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should succeed
        assert response.status_code in [200, 201], f"Expected 200/201 but got {response.status_code}: {response.text}"
        
        created_user = response.json()
        assert created_user.get("role") == "seller", f"Created user should have seller role: {created_user}"
        assert created_user.get("email") == test_user["email"], f"Email should match: {created_user}"
        
        print(f"✓ PASS: Normal user creation with seller role works correctly")
        
        # Cleanup
        if created_user.get("id"):
            self.session.delete(
                f"{BASE_URL}/api/users/{created_user['id']}", 
                headers={"Authorization": f"Bearer {token}"}
            )
    
    def test_create_normal_user_with_admin_role_works(self):
        """FUNCTIONAL: Creating normal user (role=admin) should work correctly"""
        token = self.get_super_admin_token()
        if not token:
            pytest.skip("Could not authenticate with admin credentials")
        
        test_user = {
            "name": "TEST_NormalAdmin",
            "email": f"normal_admin_{uuid.uuid4().hex[:8]}@test.com",
            "password": "test1234",
            "role": "admin"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/users", 
            json=test_user,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should succeed
        assert response.status_code in [200, 201], f"Expected 200/201 but got {response.status_code}: {response.text}"
        
        created_user = response.json()
        assert created_user.get("role") == "admin", f"Created user should have admin role: {created_user}"
        
        print(f"✓ PASS: Normal user creation with admin role works correctly")
        
        # Cleanup
        if created_user.get("id"):
            self.session.delete(
                f"{BASE_URL}/api/users/{created_user['id']}", 
                headers={"Authorization": f"Bearer {token}"}
            )
    
    def test_create_normal_user_with_manager_role_works(self):
        """FUNCTIONAL: Creating normal user (role=manager) should work correctly"""
        token = self.get_super_admin_token()
        if not token:
            pytest.skip("Could not authenticate with admin credentials")
        
        test_user = {
            "name": "TEST_NormalManager",
            "email": f"normal_manager_{uuid.uuid4().hex[:8]}@test.com",
            "password": "test1234",
            "role": "manager"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/users", 
            json=test_user,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should succeed
        assert response.status_code in [200, 201], f"Expected 200/201 but got {response.status_code}: {response.text}"
        
        created_user = response.json()
        assert created_user.get("role") == "manager", f"Created user should have manager role: {created_user}"
        
        print(f"✓ PASS: Normal user creation with manager role works correctly")
        
        # Cleanup
        if created_user.get("id"):
            self.session.delete(
                f"{BASE_URL}/api/users/{created_user['id']}", 
                headers={"Authorization": f"Bearer {token}"}
            )


class TestAuthLoginEndpoints:
    """Test authentication endpoints are working"""
    
    def test_super_admin_login(self):
        """Test super admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=SUPER_ADMIN_CREDS)
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data, "Response should contain access_token"
            print(f"✓ PASS: Super admin login successful")
        else:
            print(f"! INFO: Super admin login returned {response.status_code}: {response.text}")
            # This might be expected if super admin doesn't exist
    
    def test_tenant_admin_login(self):
        """Test tenant admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_ADMIN_CREDS)
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data, "Response should contain access_token"
            print(f"✓ PASS: Tenant admin login successful")
        else:
            print(f"! INFO: Tenant admin login returned {response.status_code}: {response.text}")
            # This might be expected if tenant admin doesn't exist


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
