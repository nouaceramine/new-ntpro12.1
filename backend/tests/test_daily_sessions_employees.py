"""
Test Daily Sessions with Employee Support
Features tested:
- POST /api/daily-sessions: Creates session linked to current user
- GET /api/daily-sessions: Returns current user's sessions only
- GET /api/daily-sessions?all_users=true: Returns all sessions (admin only)
- GET /api/daily-sessions/summary: Returns overall + per-employee report
- PUT /api/daily-sessions/:id/close: Validates user permission
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "test@test.com"
ADMIN_PASSWORD = "test123"

# Store tokens and session data
test_data = {
    "admin_token": None,
    "user2_token": None,
    "user2_id": None,
    "admin_session_id": None,
    "user2_session_id": None
}


class TestAuthSetup:
    """Get authentication tokens for testing"""
    
    def test_admin_login(self):
        """Login as admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        test_data["admin_token"] = data["access_token"]
        test_data["admin_id"] = data["user"]["id"]
        print(f"✓ Admin login successful - user_id: {data['user']['id']}")
    
    def test_create_second_user(self):
        """Create a second test user (employee) for multi-user testing"""
        if not test_data["admin_token"]:
            pytest.skip("Admin token not available")
        
        # Try to register a new user
        unique_email = f"TEST_employee_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "employee123",
            "name": "Test Employee",
            "role": "user"
        })
        
        if response.status_code == 200:
            data = response.json()
            test_data["user2_token"] = data["access_token"]
            test_data["user2_id"] = data["user"]["id"]
            test_data["user2_email"] = unique_email
            print(f"✓ Created second user: {unique_email}")
        else:
            # If registration fails, we'll just test with admin
            print(f"Note: Could not create second user (status {response.status_code})")
            test_data["user2_token"] = None


class TestDailySessionsEmployeeFeatures:
    """Test daily sessions with employee-based features"""
    
    def get_admin_headers(self):
        return {"Authorization": f"Bearer {test_data['admin_token']}"}
    
    def get_user2_headers(self):
        if test_data.get("user2_token"):
            return {"Authorization": f"Bearer {test_data['user2_token']}"}
        return None
    
    # ===== POST /api/daily-sessions =====
    
    def test_create_session_linked_to_user(self):
        """POST /api/daily-sessions - Creates session linked to current user"""
        if not test_data["admin_token"]:
            pytest.skip("Admin token not available")
        
        # First close any existing open session for admin
        response = requests.get(
            f"{BASE_URL}/api/daily-sessions/current",
            headers=self.get_admin_headers()
        )
        if response.status_code == 200 and response.json():
            session_id = response.json()["id"]
            requests.put(
                f"{BASE_URL}/api/daily-sessions/{session_id}/close",
                headers=self.get_admin_headers(),
                json={
                    "closing_cash": 100,
                    "closed_at": "2026-01-09T18:00:00Z",
                    "notes": "Cleanup for test"
                }
            )
        
        # Create a new session
        response = requests.post(
            f"{BASE_URL}/api/daily-sessions",
            headers=self.get_admin_headers(),
            json={
                "opening_cash": 1000.0,
                "opened_at": "2026-01-09T09:00:00Z"
            }
        )
        
        assert response.status_code == 200, f"Create session failed: {response.text}"
        data = response.json()
        
        # Verify user_id is set
        assert "user_id" in data, "Response should contain user_id"
        assert data["user_id"] == test_data["admin_id"], "Session should be linked to admin user"
        
        # Verify user_name is set
        assert "user_name" in data, "Response should contain user_name"
        
        test_data["admin_session_id"] = data["id"]
        print(f"✓ Session created with user_id: {data['user_id']}, user_name: {data['user_name']}")
    
    def test_create_session_prevents_duplicate_for_same_user(self):
        """POST /api/daily-sessions - Prevents duplicate open sessions for same user"""
        if not test_data["admin_token"]:
            pytest.skip("Admin token not available")
        if not test_data.get("admin_session_id"):
            pytest.skip("No admin session created")
        
        # Try to create another session for the same user
        response = requests.post(
            f"{BASE_URL}/api/daily-sessions",
            headers=self.get_admin_headers(),
            json={
                "opening_cash": 500.0,
                "opened_at": "2026-01-09T10:00:00Z"
            }
        )
        
        assert response.status_code == 400, f"Should reject duplicate session, got: {response.status_code}"
        print("✓ Duplicate session prevention working for same user")
    
    def test_create_session_allows_different_users(self):
        """POST /api/daily-sessions - Different users can have their own sessions"""
        user2_headers = self.get_user2_headers()
        if not user2_headers:
            pytest.skip("Second user not available")
        
        # Close any existing session for user2
        response = requests.get(
            f"{BASE_URL}/api/daily-sessions/current",
            headers=user2_headers
        )
        if response.status_code == 200 and response.json():
            session_id = response.json()["id"]
            requests.put(
                f"{BASE_URL}/api/daily-sessions/{session_id}/close",
                headers=user2_headers,
                json={
                    "closing_cash": 100,
                    "closed_at": "2026-01-09T18:00:00Z",
                    "notes": "Cleanup"
                }
            )
        
        # Create session for user2 (different from admin)
        response = requests.post(
            f"{BASE_URL}/api/daily-sessions",
            headers=user2_headers,
            json={
                "opening_cash": 500.0,
                "opened_at": "2026-01-09T09:30:00Z"
            }
        )
        
        assert response.status_code == 200, f"User2 session creation failed: {response.text}"
        data = response.json()
        
        assert data["user_id"] == test_data["user2_id"], "Session should be linked to user2"
        test_data["user2_session_id"] = data["id"]
        print(f"✓ Different user can create their own session: {data['user_id']}")
    
    # ===== GET /api/daily-sessions =====
    
    def test_get_sessions_returns_own_sessions_only(self):
        """GET /api/daily-sessions - Returns current user's sessions only"""
        if not test_data["admin_token"]:
            pytest.skip("Admin token not available")
        
        # Get sessions for admin (without all_users flag)
        response = requests.get(
            f"{BASE_URL}/api/daily-sessions",
            headers=self.get_admin_headers()
        )
        
        assert response.status_code == 200, f"Get sessions failed: {response.text}"
        sessions = response.json()
        
        # All sessions should belong to admin
        for session in sessions:
            # Old sessions may not have user_id
            if session.get("user_id"):
                assert session["user_id"] == test_data["admin_id"], \
                    f"Session {session['id']} belongs to {session['user_id']}, expected {test_data['admin_id']}"
        
        print(f"✓ GET sessions returns {len(sessions)} sessions for current user")
    
    def test_user2_gets_own_sessions_only(self):
        """GET /api/daily-sessions - User2 should see only their sessions"""
        user2_headers = self.get_user2_headers()
        if not user2_headers:
            pytest.skip("Second user not available")
        
        response = requests.get(
            f"{BASE_URL}/api/daily-sessions",
            headers=user2_headers
        )
        
        assert response.status_code == 200
        sessions = response.json()
        
        for session in sessions:
            if session.get("user_id"):
                assert session["user_id"] == test_data["user2_id"], \
                    "User2 should only see their own sessions"
        
        print(f"✓ User2 sees only their {len(sessions)} session(s)")
    
    # ===== GET /api/daily-sessions?all_users=true =====
    
    def test_get_all_sessions_admin_only(self):
        """GET /api/daily-sessions?all_users=true - Returns all sessions (admin only)"""
        if not test_data["admin_token"]:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/daily-sessions?all_users=true",
            headers=self.get_admin_headers()
        )
        
        assert response.status_code == 200, f"Get all sessions failed: {response.text}"
        sessions = response.json()
        
        # Should include sessions from multiple users if available
        user_ids = set()
        for session in sessions:
            if session.get("user_id"):
                user_ids.add(session["user_id"])
        
        print(f"✓ Admin can see all sessions: {len(sessions)} sessions from {len(user_ids)} users")
    
    def test_get_all_sessions_non_admin_gets_own_only(self):
        """GET /api/daily-sessions?all_users=true - Non-admin still sees only own sessions"""
        user2_headers = self.get_user2_headers()
        if not user2_headers:
            pytest.skip("Second user not available")
        
        # User2 is not admin, so all_users=true should be ignored
        response = requests.get(
            f"{BASE_URL}/api/daily-sessions?all_users=true",
            headers=user2_headers
        )
        
        assert response.status_code == 200
        sessions = response.json()
        
        # Non-admin should only see their own sessions even with all_users=true
        for session in sessions:
            if session.get("user_id"):
                assert session["user_id"] == test_data["user2_id"], \
                    "Non-admin with all_users=true should still only see own sessions"
        
        print(f"✓ Non-admin with all_users=true still sees only own sessions: {len(sessions)}")
    
    # ===== GET /api/daily-sessions/summary =====
    
    def test_get_summary_overall_and_per_employee(self):
        """GET /api/daily-sessions/summary - Returns overall + per-employee report"""
        if not test_data["admin_token"]:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/daily-sessions/summary?days=30",
            headers=self.get_admin_headers()
        )
        
        assert response.status_code == 200, f"Get summary failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "overall" in data, "Response should contain overall summary"
        assert "by_user" in data, "Response should contain per-user breakdown"
        assert "period_days" in data, "Response should contain period_days"
        
        # Verify overall fields
        overall = data["overall"]
        assert "total_sessions" in overall, "Overall should have total_sessions"
        assert "total_sales" in overall, "Overall should have total_sales"
        assert "total_cash_sales" in overall, "Overall should have total_cash_sales"
        assert "total_credit_sales" in overall, "Overall should have total_credit_sales"
        assert "total_difference" in overall, "Overall should have total_difference"
        
        # Verify by_user structure
        by_user = data["by_user"]
        assert isinstance(by_user, list), "by_user should be a list"
        
        for user_stat in by_user:
            assert "user_id" in user_stat, "User stat should have user_id"
            assert "user_name" in user_stat, "User stat should have user_name"
            assert "sessions_count" in user_stat, "User stat should have sessions_count"
            assert "total_sales" in user_stat, "User stat should have total_sales"
            assert "cash_sales" in user_stat, "User stat should have cash_sales"
            assert "credit_sales" in user_stat, "User stat should have credit_sales"
            assert "total_difference" in user_stat, "User stat should have total_difference"
        
        print(f"✓ Summary report structure verified: {len(by_user)} employee records")
        print(f"  Overall: {overall['total_sessions']} sessions, {overall['total_sales']} total sales")
    
    def test_summary_requires_admin(self):
        """GET /api/daily-sessions/summary - Requires admin access"""
        user2_headers = self.get_user2_headers()
        if not user2_headers:
            pytest.skip("Second user not available")
        
        response = requests.get(
            f"{BASE_URL}/api/daily-sessions/summary?days=7",
            headers=user2_headers
        )
        
        # Should be 403 Forbidden for non-admin
        assert response.status_code == 403, \
            f"Summary should require admin, got status {response.status_code}"
        
        print("✓ Summary endpoint requires admin access")
    
    # ===== PUT /api/daily-sessions/:id/close =====
    
    def test_close_session_validates_owner(self):
        """PUT /api/daily-sessions/:id/close - Only owner or admin can close"""
        user2_headers = self.get_user2_headers()
        if not user2_headers or not test_data.get("admin_session_id"):
            pytest.skip("Second user or admin session not available")
        
        # User2 tries to close admin's session - should fail
        response = requests.put(
            f"{BASE_URL}/api/daily-sessions/{test_data['admin_session_id']}/close",
            headers=user2_headers,
            json={
                "closing_cash": 1000,
                "closed_at": "2026-01-09T18:00:00Z",
                "notes": "Trying to close another user's session"
            }
        )
        
        assert response.status_code == 403, \
            f"User should not be able to close another user's session, got {response.status_code}"
        
        print("✓ Non-owner cannot close another user's session")
    
    def test_admin_can_close_any_session(self):
        """PUT /api/daily-sessions/:id/close - Admin can close any session"""
        if not test_data["admin_token"] or not test_data.get("user2_session_id"):
            pytest.skip("Admin token or user2 session not available")
        
        # Admin closes user2's session
        response = requests.put(
            f"{BASE_URL}/api/daily-sessions/{test_data['user2_session_id']}/close",
            headers=self.get_admin_headers(),
            json={
                "closing_cash": 500,
                "closed_at": "2026-01-09T18:00:00Z",
                "notes": "Admin closing employee session"
            }
        )
        
        assert response.status_code == 200, f"Admin should be able to close any session: {response.text}"
        
        print("✓ Admin can close any user's session")
    
    def test_owner_can_close_own_session(self):
        """PUT /api/daily-sessions/:id/close - Owner can close own session"""
        if not test_data["admin_token"] or not test_data.get("admin_session_id"):
            pytest.skip("Admin token or admin session not available")
        
        response = requests.put(
            f"{BASE_URL}/api/daily-sessions/{test_data['admin_session_id']}/close",
            headers=self.get_admin_headers(),
            json={
                "closing_cash": 1050,
                "closed_at": "2026-01-09T18:30:00Z",
                "notes": "Owner closing own session"
            }
        )
        
        assert response.status_code == 200, f"Owner should be able to close own session: {response.text}"
        data = response.json()
        
        # Verify the session is closed
        assert data["status"] == "closed", "Session should be marked as closed"
        assert data["closing_cash"] == 1050, "Closing cash should be saved"
        
        print("✓ Owner can close their own session")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_user(self):
        """Delete test user created for this test"""
        if not test_data["admin_token"] or not test_data.get("user2_id"):
            pytest.skip("Nothing to clean up")
        
        response = requests.delete(
            f"{BASE_URL}/api/users/{test_data['user2_id']}",
            headers={"Authorization": f"Bearer {test_data['admin_token']}"}
        )
        
        # May fail if user has data - that's ok
        print(f"✓ Cleanup attempted for test user: status {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
