"""
Tests for Robot API endpoints and Robot Manager
"""
import pytest
import httpx
import asyncio

API_URL = "https://nt-commerce-refactor.preview.emergentagent.com"
ADMIN_EMAIL = "admin@ntcommerce.com"
ADMIN_PASSWORD = "Admin@2024"


@pytest.fixture
def admin_token():
    resp = httpx.post(f"{API_URL}/api/auth/unified-login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestRobotStatus:
    def test_get_status(self, admin_token):
        resp = httpx.get(f"{API_URL}/api/robots/status", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "robots" in data
        assert "inventory" in data["robots"]
        assert "debt" in data["robots"]
        assert "report" in data["robots"]
        assert data["is_running"] is True

    def test_status_requires_auth(self):
        resp = httpx.get(f"{API_URL}/api/robots/status")
        assert resp.status_code in [401, 403]


class TestRobotRun:
    def test_run_inventory(self, admin_token):
        resp = httpx.post(f"{API_URL}/api/robots/run/inventory", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "stats" in data
        assert data["stats"]["checks"] >= 1

    def test_run_debt(self, admin_token):
        resp = httpx.post(f"{API_URL}/api/robots/run/debt", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        assert "stats" in resp.json()

    def test_run_report(self, admin_token):
        resp = httpx.post(f"{API_URL}/api/robots/run/report", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        assert "stats" in resp.json()

    def test_run_invalid_robot(self, admin_token):
        resp = httpx.post(f"{API_URL}/api/robots/run/nonexistent", headers=auth_headers(admin_token))
        assert resp.status_code == 404


class TestRobotRestart:
    def test_restart_inventory(self, admin_token):
        resp = httpx.post(f"{API_URL}/api/robots/restart/inventory", headers=auth_headers(admin_token))
        assert resp.status_code == 200

    def test_restart_invalid(self, admin_token):
        resp = httpx.post(f"{API_URL}/api/robots/restart/nonexistent", headers=auth_headers(admin_token))
        assert resp.status_code == 404


class TestRobotLifecycle:
    def test_stop_and_start(self, admin_token):
        # Stop all
        resp = httpx.post(f"{API_URL}/api/robots/stop-all", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        # Check status
        resp = httpx.get(f"{API_URL}/api/robots/status", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        assert resp.json()["is_running"] is False
        # Start all
        resp = httpx.post(f"{API_URL}/api/robots/start-all", headers=auth_headers(admin_token))
        assert resp.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
