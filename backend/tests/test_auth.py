"""
Tests for authentication and core endpoints
"""
import pytest
import httpx

API_URL = "https://legendary-build-1.preview.emergentagent.com"


class TestAuth:
    def test_admin_login(self):
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": "admin@ntcommerce.com", "password": "Admin@2024"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user_type"] == "admin"

    def test_tenant_login(self):
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": "ncr@ntcommerce.com", "password": "Test@123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    def test_invalid_login(self):
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": "wrong@email.com", "password": "wrong"
        })
        assert resp.status_code in [401, 404]

    def test_get_me(self):
        login = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": "admin@ntcommerce.com", "password": "Admin@2024"
        })
        token = login.json()["access_token"]
        resp = httpx.get(f"{API_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "admin@ntcommerce.com"


class TestProducts:
    @pytest.fixture
    def tenant_token(self):
        resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
            "email": "ncr@ntcommerce.com", "password": "Test@123"
        })
        return resp.json()["access_token"]

    def test_get_products(self, tenant_token):
        resp = httpx.get(f"{API_URL}/api/products", headers={"Authorization": f"Bearer {tenant_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
