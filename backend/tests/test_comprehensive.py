"""
Comprehensive test suite for NT Commerce - covers all major features
Run: cd /app/backend && python -m pytest tests/test_comprehensive.py -v
"""
import pytest
import httpx
import pyotp

API_URL = "https://legendary-build-1.preview.emergentagent.com"
ADMIN = {"email": "admin@ntcommerce.com", "password": "Admin@2024"}
TENANT = {"email": "ncr@ntcommerce.com", "password": "Test@123"}


@pytest.fixture(scope="module")
def admin_token():
    resp = httpx.post(f"{API_URL}/api/auth/unified-login", json=ADMIN)
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def tenant_token():
    resp = httpx.post(f"{API_URL}/api/auth/unified-login", json=TENANT)
    assert resp.status_code == 200
    return resp.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ═══════════ AUTH ═══════════
class TestAuth:
    def test_admin_login(self):
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json=ADMIN)
        assert resp.status_code == 200
        d = resp.json()
        assert "access_token" in d
        assert d["user_type"] == "admin"

    def test_tenant_login(self):
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json=TENANT)
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_invalid_login(self):
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={"email": "no@no.com", "password": "x"})
        assert resp.status_code == 401

    def test_get_me(self, admin_token):
        resp = httpx.get(f"{API_URL}/api/auth/me", headers=auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["email"] == ADMIN["email"]


# ═══════════ BRUTE FORCE ═══════════
class TestBruteForce:
    def test_lockout_after_5_fails(self):
        email = "brutetest@fake.com"
        for _ in range(6):
            resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={"email": email, "password": "wrong"})
        assert resp.status_code == 429

    def test_real_accounts_not_affected(self):
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json=ADMIN)
        assert resp.status_code == 200


# ═══════════ 2FA ═══════════
class TestTwoFA:
    def test_2fa_status(self, admin_token):
        resp = httpx.get(f"{API_URL}/api/auth/2fa/status", headers=auth(admin_token))
        assert resp.status_code == 200
        assert "enabled" in resp.json()

    def test_2fa_setup(self, admin_token):
        resp = httpx.post(f"{API_URL}/api/auth/2fa/setup", headers=auth(admin_token))
        assert resp.status_code == 200
        d = resp.json()
        assert "secret" in d
        assert "qr_code" in d
        assert d["qr_code"].startswith("data:image/png;base64,")

    def test_2fa_verify_wrong_code(self, admin_token):
        resp = httpx.post(f"{API_URL}/api/auth/2fa/verify", json={"code": "000000"}, headers=auth(admin_token))
        assert resp.status_code == 400


# ═══════════ ROBOTS ═══════════
class TestRobots:
    def test_status_6_robots(self, admin_token):
        resp = httpx.get(f"{API_URL}/api/robots/status", headers=auth(admin_token))
        assert resp.status_code == 200
        d = resp.json()
        assert len(d["robots"]) == 6
        for name in ["inventory", "debt", "report", "customer", "pricing", "maintenance"]:
            assert name in d["robots"]

    def test_run_all_robots(self, admin_token):
        for name in ["inventory", "debt", "report", "customer", "pricing", "maintenance"]:
            resp = httpx.post(f"{API_URL}/api/robots/run/{name}", headers=auth(admin_token))
            assert resp.status_code == 200
            assert "stats" in resp.json()

    def test_restart_robot(self, admin_token):
        resp = httpx.post(f"{API_URL}/api/robots/restart/inventory", headers=auth(admin_token))
        assert resp.status_code == 200

    def test_invalid_robot(self, admin_token):
        resp = httpx.post(f"{API_URL}/api/robots/run/fake", headers=auth(admin_token))
        assert resp.status_code == 404

    def test_requires_admin(self):
        resp = httpx.get(f"{API_URL}/api/robots/status")
        assert resp.status_code in [401, 403]


# ═══════════ AUTO REPORTS ═══════════
class TestAutoReports:
    def test_get_reports(self, admin_token):
        resp = httpx.get(f"{API_URL}/api/auto-reports", headers=auth(admin_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_filter_by_type(self, admin_token):
        resp = httpx.get(f"{API_URL}/api/auto-reports?report_type=daily", headers=auth(admin_token))
        assert resp.status_code == 200

    def test_collection_reports(self, admin_token):
        resp = httpx.get(f"{API_URL}/api/collection-reports", headers=auth(admin_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ═══════════ PRODUCTS (Tenant) ═══════════
class TestProducts:
    def test_list_products(self, tenant_token):
        resp = httpx.get(f"{API_URL}/api/products", headers=auth(tenant_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_paginated_products(self, tenant_token):
        resp = httpx.get(f"{API_URL}/api/products/paginated?page=1&page_size=5", headers=auth(tenant_token))
        assert resp.status_code == 200


# ═══════════ CUSTOMERS (Tenant) ═══════════
class TestCustomers:
    def test_list_customers(self, tenant_token):
        resp = httpx.get(f"{API_URL}/api/customers", headers=auth(tenant_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ═══════════ SALES (Tenant) ═══════════
class TestSales:
    def test_list_sales(self, tenant_token):
        resp = httpx.get(f"{API_URL}/api/sales", headers=auth(tenant_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
