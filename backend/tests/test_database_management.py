"""
Database Management System API Tests
Tests for GET /api/saas/databases, /api/saas/databases/stats, /api/saas/databases/logs
Tests for POST /api/saas/databases/{db_id}/backup, /api/saas/databases/{db_id}/freeze
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDatabaseManagementAPIs:
    """Tests for Database Management System APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - Login as saas_admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as saas_admin using /api/auth/login
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "super@ntcommerce.com", "password": "admin123"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
    
    def test_saas_admin_login(self):
        """Test saas_admin login with super@ntcommerce.com / admin123"""
        response = requests.post(
            f"{BASE_URL}/api/saas-admin/login",
            json={"email": "super@ntcommerce.com", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        print(f"✓ Login successful, token received")
    
    def test_get_all_databases(self):
        """Test GET /api/saas/databases - list all databases"""
        response = self.session.get(f"{BASE_URL}/api/saas/databases")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Should have at least main database
        assert len(data) >= 1, "Should have at least main database"
        
        # Check main database structure
        main_db = next((db for db in data if db.get("id") == "main"), None)
        assert main_db is not None, "Main database not found"
        assert main_db.get("type") == "main", "Main db should have type 'main'"
        assert main_db.get("display_name") == "قاعدة البيانات الرئيسية"
        
        # Check required fields
        required_fields = ["id", "name", "display_name", "type", "size_mb", 
                         "collections_count", "documents_count", "status", "is_active"]
        for field in required_fields:
            assert field in main_db, f"Missing field: {field}"
        
        print(f"✓ GET /api/saas/databases - Found {len(data)} databases")
        print(f"  - Main DB size: {main_db.get('size_mb')} MB")
        print(f"  - Collections: {main_db.get('collections_count')}")
        print(f"  - Documents: {main_db.get('documents_count')}")
    
    def test_get_database_stats(self):
        """Test GET /api/saas/databases/stats - get overall statistics"""
        response = self.session.get(f"{BASE_URL}/api/saas/databases/stats")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Check required fields
        required_fields = ["total_databases", "total_size", "active_databases", 
                         "inactive_databases", "total_backups", "alerts_count"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Validate types
        assert isinstance(data["total_databases"], int), "total_databases should be int"
        assert isinstance(data["total_size"], (int, float)), "total_size should be number"
        assert isinstance(data["active_databases"], int), "active_databases should be int"
        
        print(f"✓ GET /api/saas/databases/stats")
        print(f"  - Total databases: {data['total_databases']}")
        print(f"  - Total size: {data['total_size']} MB")
        print(f"  - Active: {data['active_databases']}")
        print(f"  - Inactive: {data['inactive_databases']}")
        print(f"  - Backups: {data['total_backups']}")
        print(f"  - Alerts: {data['alerts_count']}")
    
    def test_get_database_logs(self):
        """Test GET /api/saas/databases/logs - get operation logs"""
        response = self.session.get(f"{BASE_URL}/api/saas/databases/logs")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # If there are logs, check structure
        if len(data) > 0:
            log = data[0]
            required_fields = ["id", "operation", "database_id", "status", "created_at"]
            for field in required_fields:
                assert field in log, f"Missing field in log: {field}"
        
        print(f"✓ GET /api/saas/databases/logs - Found {len(data)} logs")
    
    def test_get_database_backups(self):
        """Test GET /api/saas/databases/backups - get backup list"""
        response = self.session.get(f"{BASE_URL}/api/saas/databases/backups")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # If there are backups, check structure
        if len(data) > 0:
            backup = data[0]
            required_fields = ["id", "database_id", "database_name", "status", "created_at"]
            for field in required_fields:
                assert field in backup, f"Missing field in backup: {field}"
        
        print(f"✓ GET /api/saas/databases/backups - Found {len(data)} backups")
    
    def test_create_backup_main_database(self):
        """Test POST /api/saas/databases/main/backup - create backup for main database"""
        response = self.session.post(f"{BASE_URL}/api/saas/databases/main/backup", json={})
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should have message"
        assert "backup_id" in data, "Response should have backup_id"
        
        print(f"✓ POST /api/saas/databases/main/backup")
        print(f"  - Backup ID: {data.get('backup_id')}")
        print(f"  - Size: {data.get('size_mb')} MB")
        
        # Verify backup appears in list
        backups_response = self.session.get(f"{BASE_URL}/api/saas/databases/backups")
        if backups_response.status_code == 200:
            backups = backups_response.json()
            backup_found = any(b.get("id") == data.get("backup_id") for b in backups)
            assert backup_found, "Created backup should appear in backup list"
            print(f"  - Verified backup in list: ✓")
    
    def test_freeze_unfreeze_database(self):
        """Test POST /api/saas/databases/{db_id}/freeze - freeze/unfreeze tenant database"""
        # First get a tenant database ID
        db_response = self.session.get(f"{BASE_URL}/api/saas/databases")
        assert db_response.status_code == 200
        
        databases = db_response.json()
        tenant_db = next((db for db in databases if db.get("type") == "tenant"), None)
        
        if tenant_db is None:
            pytest.skip("No tenant database found to test freeze/unfreeze")
        
        db_id = tenant_db["id"]
        
        # Test freeze
        freeze_response = self.session.post(
            f"{BASE_URL}/api/saas/databases/{db_id}/freeze",
            json={"freeze": True}
        )
        assert freeze_response.status_code == 200, f"Freeze failed: {freeze_response.text}"
        print(f"✓ POST /api/saas/databases/{db_id}/freeze (freeze=True)")
        
        # Test unfreeze
        unfreeze_response = self.session.post(
            f"{BASE_URL}/api/saas/databases/{db_id}/freeze",
            json={"freeze": False}
        )
        assert unfreeze_response.status_code == 200, f"Unfreeze failed: {unfreeze_response.text}"
        print(f"✓ POST /api/saas/databases/{db_id}/freeze (freeze=False)")
    
    def test_cannot_freeze_main_database(self):
        """Test that main database cannot be frozen"""
        response = self.session.post(
            f"{BASE_URL}/api/saas/databases/main/freeze",
            json={"freeze": True}
        )
        assert response.status_code == 400, f"Should fail with 400, got: {response.status_code}"
        print(f"✓ Main database correctly rejects freeze operation (400)")
    
    def test_export_main_database(self):
        """Test GET /api/saas/databases/main/export - export database to JSON"""
        response = self.session.get(f"{BASE_URL}/api/saas/databases/main/export")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, f"Expected JSON, got: {content_type}"
        
        # Check content disposition for download
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition, "Should be a downloadable file"
        
        print(f"✓ GET /api/saas/databases/main/export")
        print(f"  - Content-Type: {content_type}")
        print(f"  - Content-Disposition: {content_disposition[:50]}...")
    
    def test_backup_creates_operation_log(self):
        """Test that backup operation creates log entry"""
        # Get logs before
        logs_before = self.session.get(f"{BASE_URL}/api/saas/databases/logs").json()
        
        # Create backup
        backup_response = self.session.post(f"{BASE_URL}/api/saas/databases/main/backup", json={})
        assert backup_response.status_code == 200
        
        # Get logs after
        logs_after = self.session.get(f"{BASE_URL}/api/saas/databases/logs").json()
        
        # Should have more logs
        assert len(logs_after) > len(logs_before), "Backup should create operation log"
        
        # Find backup log
        backup_log = next((log for log in logs_after if log.get("operation") == "backup"), None)
        assert backup_log is not None, "Backup operation log not found"
        assert backup_log.get("status") == "success", "Backup log should show success"
        
        print(f"✓ Backup operation creates log entry")
        print(f"  - Operation: {backup_log.get('operation')}")
        print(f"  - Status: {backup_log.get('status')}")


class TestDatabaseManagementUnauthorized:
    """Test unauthorized access to database management APIs"""
    
    def test_databases_without_auth(self):
        """Test GET /api/saas/databases without authentication"""
        response = requests.get(f"{BASE_URL}/api/saas/databases")
        assert response.status_code in [401, 403], f"Should be unauthorized, got: {response.status_code}"
        print(f"✓ /api/saas/databases correctly rejects unauthenticated requests")
    
    def test_stats_without_auth(self):
        """Test GET /api/saas/databases/stats without authentication"""
        response = requests.get(f"{BASE_URL}/api/saas/databases/stats")
        assert response.status_code in [401, 403], f"Should be unauthorized, got: {response.status_code}"
        print(f"✓ /api/saas/databases/stats correctly rejects unauthenticated requests")
    
    def test_backup_without_auth(self):
        """Test POST /api/saas/databases/main/backup without authentication"""
        response = requests.post(f"{BASE_URL}/api/saas/databases/main/backup", json={})
        assert response.status_code in [401, 403], f"Should be unauthorized, got: {response.status_code}"
        print(f"✓ /api/saas/databases/main/backup correctly rejects unauthenticated requests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
