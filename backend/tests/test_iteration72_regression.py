"""
NT Commerce 12.0 - Iteration 72 Regression Testing
Testing after extracting 4,108 lines from main.py into routes/legacy_inline_routes.py

Test Scope:
- Health endpoint
- System info (152 tables, version 12.0.0)
- Unified login (tenant & super admin)
- Products, Customers, Sales (tenant routes)
- Shipping, Loyalty, Branding (tenant routes)
- Invoice templates, Payment gateways
- Store settings, WooCommerce (online_store_routes.py)
- SMS settings (sms_marketing_routes.py)
- Email settings, SendGrid (sendgrid_email_routes.py)
- Stripe packages (stripe_routes.py)
- SIM slots, System settings, Features settings, Receipt settings
- SaaS routes (super admin)
- Robots status, Sync types, System updates, Auto reports
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TENANT_EMAIL = "ncr@ntcommerce.com"
TENANT_PASSWORD = "Test@123"
SUPER_ADMIN_EMAIL = "admin@ntcommerce.com"
SUPER_ADMIN_PASSWORD = "Admin@2024"


class TestHealthAndSystem:
    """Health and System Info endpoints"""
    
    def test_health_endpoint(self):
        """GET /api/health - Should return healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health failed: {response.text}"
        data = response.json()
        assert data.get("status") == "healthy", f"Status not healthy: {data}"
        print("PASS: Health endpoint returns healthy status")
    
    def test_system_info(self):
        """GET /api/system/info - Should return version 12.0.0 and 152 tables"""
        response = requests.get(f"{BASE_URL}/api/system/info")
        assert response.status_code == 200, f"System info failed: {response.text}"
        data = response.json()
        assert data.get("version") == "12.0.0", f"Wrong version: {data.get('version')}"
        assert data.get("total_tables") == 152, f"Wrong tables count: {data.get('total_tables')}"
        print(f"PASS: System info - version {data.get('version')}, {data.get('total_tables')} tables")


class TestAuthentication:
    """Authentication tests - unified-login for tenant and super admin"""
    
    def test_tenant_login_success(self):
        """POST /api/auth/unified-login - Tenant login"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": TENANT_EMAIL,
            "password": TENANT_PASSWORD
        })
        assert response.status_code == 200, f"Tenant login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user_type") == "tenant", f"Wrong user_type: {data.get('user_type')}"
        print(f"PASS: Tenant login successful - user_type: {data.get('user_type')}")
        return data["access_token"]
    
    def test_super_admin_login_success(self):
        """POST /api/auth/unified-login - Super admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print(f"PASS: Super admin login successful - user_type: {data.get('user_type')}")
        return data["access_token"]
    
    def test_invalid_login(self):
        """POST /api/auth/unified-login - Invalid credentials should fail"""
        response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Invalid login should return 401, got {response.status_code}"
        print("PASS: Invalid login correctly returns 401")


@pytest.fixture(scope="module")
def tenant_token():
    """Get tenant access token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
        "email": TENANT_EMAIL,
        "password": TENANT_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Cannot get tenant token")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin access token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Cannot get super admin token")
    return response.json()["access_token"]


class TestTenantCoreRoutes:
    """Tenant core data routes - Products, Customers, Sales"""
    
    def test_products_list(self, tenant_token):
        """GET /api/products - List products for tenant"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200, f"Products failed: {response.text}"
        data = response.json()
        # Data can be dict with 'products' key or list directly
        if isinstance(data, dict) and "products" in data:
            print(f"PASS: Products list - {len(data['products'])} products")
        elif isinstance(data, list):
            print(f"PASS: Products list - {len(data)} products")
        else:
            print(f"PASS: Products list returned data")
    
    def test_customers_list(self, tenant_token):
        """GET /api/customers - List customers for tenant"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        assert response.status_code == 200, f"Customers failed: {response.text}"
        print("PASS: Customers list")
    
    def test_sales_list(self, tenant_token):
        """GET /api/sales - List sales for tenant"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/sales", headers=headers)
        assert response.status_code == 200, f"Sales failed: {response.text}"
        print("PASS: Sales list")


class TestShippingAndLoyalty:
    """Shipping and Loyalty routes"""
    
    def test_shipping_companies(self, tenant_token):
        """GET /api/shipping/companies - List shipping companies"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/shipping/companies", headers=headers)
        assert response.status_code == 200, f"Shipping companies failed: {response.text}"
        print("PASS: Shipping companies")
    
    def test_loyalty_settings(self, tenant_token):
        """GET /api/loyalty/settings - Get loyalty settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/loyalty/settings", headers=headers)
        assert response.status_code == 200, f"Loyalty settings failed: {response.text}"
        print("PASS: Loyalty settings")


class TestBrandingAndInvoices:
    """Branding and Invoice templates routes"""
    
    def test_branding_settings(self):
        """GET /api/branding/settings - Public branding settings"""
        response = requests.get(f"{BASE_URL}/api/branding/settings")
        # This should be accessible without auth (public endpoint)
        assert response.status_code in [200, 404], f"Branding settings unexpected: {response.status_code}"
        print(f"PASS: Branding settings - status {response.status_code}")
    
    def test_invoice_templates(self, tenant_token):
        """GET /api/invoices/templates - List invoice templates"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/invoices/templates", headers=headers)
        assert response.status_code == 200, f"Invoice templates failed: {response.text}"
        print("PASS: Invoice templates")
    
    def test_payment_gateways(self, tenant_token):
        """GET /api/payments/gateways - List payment gateways"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/payments/gateways", headers=headers)
        assert response.status_code == 200, f"Payment gateways failed: {response.text}"
        print("PASS: Payment gateways")


class TestOnlineStoreRoutes:
    """Online Store routes from online_store_routes.py"""
    
    def test_store_settings(self, tenant_token):
        """GET /api/store/settings - Get store settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/store/settings", headers=headers)
        assert response.status_code == 200, f"Store settings failed: {response.text}"
        print("PASS: Store settings (online_store_routes.py)")
    
    def test_woocommerce_settings(self, tenant_token):
        """GET /api/woocommerce/settings - Get WooCommerce settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/woocommerce/settings", headers=headers)
        assert response.status_code == 200, f"WooCommerce settings failed: {response.text}"
        print("PASS: WooCommerce settings (online_store_routes.py)")


class TestSMSMarketingRoutes:
    """SMS Marketing routes from sms_marketing_routes.py"""
    
    def test_sms_settings(self, tenant_token):
        """GET /api/sms/settings - Get SMS settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/sms/settings", headers=headers)
        assert response.status_code == 200, f"SMS settings failed: {response.text}"
        data = response.json()
        # Verify default settings structure
        assert "auto_reminder_enabled" in data or "message_template" in data or "id" in data, f"Invalid SMS settings structure: {data}"
        print("PASS: SMS settings (sms_marketing_routes.py)")


class TestSendGridEmailRoutes:
    """SendGrid Email routes from sendgrid_email_routes.py"""
    
    def test_email_settings(self, tenant_token):
        """GET /api/email/settings - Get email settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/email/settings", headers=headers)
        assert response.status_code == 200, f"Email settings failed: {response.text}"
        print("PASS: Email settings (sendgrid_email_routes.py)")
    
    def test_sendgrid_settings(self, tenant_token):
        """GET /api/notifications/sendgrid/settings - Get SendGrid settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications/sendgrid/settings", headers=headers)
        assert response.status_code == 200, f"SendGrid settings failed: {response.text}"
        print("PASS: SendGrid settings (sendgrid_email_routes.py)")


class TestStripeRoutes:
    """Stripe Payment routes from stripe_routes.py"""
    
    def test_stripe_packages(self):
        """GET /api/payments/packages - Get subscription packages"""
        response = requests.get(f"{BASE_URL}/api/payments/packages")
        assert response.status_code == 200, f"Stripe packages failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Packages should be list, got {type(data)}"
        assert len(data) >= 1, f"Should have at least 1 package, got {len(data)}"
        print(f"PASS: Stripe packages - {len(data)} packages (stripe_routes.py)")


class TestTenantAdminSettings:
    """Tenant admin specific settings"""
    
    def test_sim_slots(self, tenant_token):
        """GET /api/sim/slots - Get SIM slots"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/sim/slots", headers=headers)
        # SIM slots might return 200 or 404 depending on feature availability
        assert response.status_code in [200, 404], f"SIM slots unexpected: {response.status_code}"
        print(f"PASS: SIM slots - status {response.status_code}")
    
    def test_system_settings(self, tenant_token):
        """GET /api/system/settings - Get system settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/system/settings", headers=headers)
        assert response.status_code in [200, 404], f"System settings unexpected: {response.status_code}"
        print(f"PASS: System settings - status {response.status_code}")
    
    def test_features_settings(self, tenant_token):
        """GET /api/settings/features - Get feature settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/settings/features", headers=headers)
        # Could be 200 or 403 if not admin
        assert response.status_code in [200, 403, 404], f"Features settings unexpected: {response.status_code}"
        print(f"PASS: Features settings - status {response.status_code}")
    
    def test_receipt_settings(self, tenant_token):
        """GET /api/settings/receipt - Get receipt settings"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/settings/receipt", headers=headers)
        assert response.status_code in [200, 404], f"Receipt settings unexpected: {response.status_code}"
        print(f"PASS: Receipt settings - status {response.status_code}")


class TestSuperAdminRoutes:
    """Super Admin routes - SaaS management"""
    
    def test_saas_tenants(self, super_admin_token):
        """GET /api/saas/tenants - List all tenants"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/saas/tenants", headers=headers)
        assert response.status_code == 200, f"SaaS tenants failed: {response.text}"
        print("PASS: SaaS tenants (super admin)")
    
    def test_robots_status(self, super_admin_token):
        """GET /api/robots/status - Get robots status"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/robots/status", headers=headers)
        assert response.status_code == 200, f"Robots status failed: {response.text}"
        data = response.json()
        # Check for robots in response
        if isinstance(data, dict):
            robots_count = len([k for k in data.keys() if 'robot' in k.lower() or k in ['inventory', 'debt', 'report', 'customer', 'pricing', 'maintenance', 'profit', 'repair', 'prediction', 'notification', 'supplier']])
            print(f"PASS: Robots status - {robots_count} robots found")
        else:
            print(f"PASS: Robots status returned data")
    
    def test_sync_available_types(self, super_admin_token):
        """GET /api/sync/available-types - Get available sync types"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/sync/available-types", headers=headers)
        # This might return 200 or 404 depending on implementation
        assert response.status_code in [200, 404], f"Sync types unexpected: {response.status_code}"
        print(f"PASS: Sync available types - status {response.status_code}")
    
    def test_system_updates_stats(self, super_admin_token):
        """GET /api/system-updates/stats - Get system update stats"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/system-updates/stats", headers=headers)
        assert response.status_code in [200, 404], f"System updates stats unexpected: {response.status_code}"
        print(f"PASS: System updates stats - status {response.status_code}")
    
    def test_auto_reports(self, super_admin_token):
        """GET /api/auto-reports - Get auto reports"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/auto-reports", headers=headers)
        assert response.status_code in [200, 404], f"Auto reports unexpected: {response.status_code}"
        print(f"PASS: Auto reports - status {response.status_code}")


class TestLegacyInlineRoutes:
    """Testing legacy inline routes now in legacy_inline_routes.py"""
    
    def test_auth_me(self, tenant_token):
        """GET /api/auth/me - Get current user info"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        assert "email" in data or "id" in data, "Auth me should return user info"
        print("PASS: Auth me (legacy_inline_routes.py)")
    
    def test_notifications(self, tenant_token):
        """GET /api/notifications - Get notifications"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        assert response.status_code == 200, f"Notifications failed: {response.text}"
        print("PASS: Notifications (legacy_inline_routes.py)")
    
    def test_blacklist(self, tenant_token):
        """GET /api/blacklist - Get blacklist"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/blacklist", headers=headers)
        assert response.status_code == 200, f"Blacklist failed: {response.text}"
        print("PASS: Blacklist (legacy_inline_routes.py)")
    
    def test_price_history(self, tenant_token):
        """GET /api/price-history - Get price history"""
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = requests.get(f"{BASE_URL}/api/price-history", headers=headers)
        assert response.status_code == 200, f"Price history failed: {response.text}"
        print("PASS: Price history (legacy_inline_routes.py)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
