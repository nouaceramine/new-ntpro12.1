"""
Test pagination APIs for Products and Customers
Tests the newly implemented pagination endpoints and the Pagination component integration
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
LOGIN_URL = f"{BASE_URL}/api/auth/login"
PRODUCTS_PAGINATED_URL = f"{BASE_URL}/api/products/paginated"
CUSTOMERS_PAGINATED_URL = f"{BASE_URL}/api/customers/paginated"
PRODUCTS_URL = f"{BASE_URL}/api/products"
CUSTOMERS_URL = f"{BASE_URL}/api/customers"

# Test credentials
TEST_EMAIL = "admin@test.com"
TEST_PASSWORD = "password"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(LOGIN_URL, json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestProductsPagination:
    """Test Products Paginated API endpoint"""
    
    def test_products_paginated_default_params(self):
        """Test /api/products/paginated with default parameters"""
        response = requests.get(PRODUCTS_PAGINATED_URL)
        
        # Should return 200 (no auth required for products)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Validate response structure
        assert "items" in data, "Response should have 'items' field"
        assert "total" in data, "Response should have 'total' field"
        assert "page" in data, "Response should have 'page' field"
        assert "page_size" in data, "Response should have 'page_size' field"
        assert "total_pages" in data, "Response should have 'total_pages' field"
        
        # Validate default values
        assert data["page"] == 1, "Default page should be 1"
        assert data["page_size"] == 20, "Default page_size should be 20"
        assert isinstance(data["items"], list), "items should be a list"
        assert isinstance(data["total"], int), "total should be an integer"
        assert isinstance(data["total_pages"], int), "total_pages should be an integer"
        
        print(f"Products paginated: total={data['total']}, page={data['page']}, page_size={data['page_size']}, items_returned={len(data['items'])}")
    
    def test_products_paginated_custom_page_size(self):
        """Test /api/products/paginated with page_size=5"""
        response = requests.get(f"{PRODUCTS_PAGINATED_URL}?page=1&page_size=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page_size"] == 5, "page_size should be 5"
        assert len(data["items"]) <= 5, "Should return at most 5 items"
        
        # Calculate expected total pages
        if data["total"] > 0:
            expected_total_pages = (data["total"] + 5 - 1) // 5
            assert data["total_pages"] == expected_total_pages, f"total_pages should be {expected_total_pages}"
        
        print(f"With page_size=5: total={data['total']}, total_pages={data['total_pages']}, items_returned={len(data['items'])}")
    
    def test_products_paginated_page_2(self):
        """Test /api/products/paginated page 2"""
        # First get page 1 to understand the data
        page1_response = requests.get(f"{PRODUCTS_PAGINATED_URL}?page=1&page_size=5")
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        
        if page1_data["total_pages"] > 1:
            # Get page 2
            page2_response = requests.get(f"{PRODUCTS_PAGINATED_URL}?page=2&page_size=5")
            assert page2_response.status_code == 200
            page2_data = page2_response.json()
            
            assert page2_data["page"] == 2, "Page should be 2"
            
            # Items on page 2 should be different from page 1
            if len(page1_data["items"]) > 0 and len(page2_data["items"]) > 0:
                page1_ids = [item["id"] for item in page1_data["items"]]
                page2_ids = [item["id"] for item in page2_data["items"]]
                # No overlap between pages
                assert set(page1_ids).isdisjoint(set(page2_ids)), "Page 1 and Page 2 should have different items"
                print(f"Page 2 has {len(page2_data['items'])} items, no overlap with page 1")
        else:
            print("Not enough products for page 2 test, skipping")
    
    def test_products_paginated_with_search(self):
        """Test /api/products/paginated with search parameter"""
        response = requests.get(f"{PRODUCTS_PAGINATED_URL}?search=test&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate structure even with search
        assert "items" in data
        assert "total" in data
        print(f"Search 'test': found {data['total']} matching products")
    
    def test_products_paginated_edge_case_large_page(self):
        """Test requesting a page number beyond available pages"""
        response = requests.get(f"{PRODUCTS_PAGINATED_URL}?page=9999&page_size=5")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty items for page beyond total
        assert data["page"] == 9999, "Should respect the requested page number"
        assert len(data["items"]) == 0, "Should return empty items for page beyond total"
        print(f"Edge case - page 9999: items returned = {len(data['items'])}")


class TestCustomersPagination:
    """Test Customers Paginated API endpoint (requires authentication)"""
    
    def test_customers_paginated_requires_auth(self):
        """Test that /api/customers/paginated requires authentication"""
        response = requests.get(CUSTOMERS_PAGINATED_URL)
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"Auth required for customers: status={response.status_code}")
    
    def test_customers_paginated_default_params(self, auth_headers):
        """Test /api/customers/paginated with default parameters (authenticated)"""
        response = requests.get(CUSTOMERS_PAGINATED_URL, headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Validate response structure
        assert "items" in data, "Response should have 'items' field"
        assert "total" in data, "Response should have 'total' field"
        assert "page" in data, "Response should have 'page' field"
        assert "page_size" in data, "Response should have 'page_size' field"
        assert "total_pages" in data, "Response should have 'total_pages' field"
        
        # Validate default values
        assert data["page"] == 1, "Default page should be 1"
        assert data["page_size"] == 20, "Default page_size should be 20"
        
        print(f"Customers paginated: total={data['total']}, page={data['page']}, page_size={data['page_size']}, items_returned={len(data['items'])}")
    
    def test_customers_paginated_custom_page_size(self, auth_headers):
        """Test /api/customers/paginated with page_size=5"""
        response = requests.get(f"{CUSTOMERS_PAGINATED_URL}?page=1&page_size=5", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page_size"] == 5, "page_size should be 5"
        assert len(data["items"]) <= 5, "Should return at most 5 items"
        
        print(f"With page_size=5: total={data['total']}, total_pages={data['total_pages']}, items_returned={len(data['items'])}")
    
    def test_customers_paginated_with_search(self, auth_headers):
        """Test /api/customers/paginated with search parameter"""
        response = requests.get(f"{CUSTOMERS_PAGINATED_URL}?search=test&page_size=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        print(f"Search 'test': found {data['total']} matching customers")


class TestPaginationConsistency:
    """Test pagination consistency between regular and paginated endpoints"""
    
    def test_products_total_matches_regular_endpoint(self):
        """Verify total count in paginated matches regular products list"""
        # Get all products (non-paginated)
        regular_response = requests.get(PRODUCTS_URL)
        assert regular_response.status_code == 200
        regular_data = regular_response.json()
        
        # Get paginated products
        paginated_response = requests.get(PRODUCTS_PAGINATED_URL)
        assert paginated_response.status_code == 200
        paginated_data = paginated_response.json()
        
        # Total should match
        assert paginated_data["total"] == len(regular_data), \
            f"Paginated total ({paginated_data['total']}) should match regular endpoint count ({len(regular_data)})"
        
        print(f"Consistency check: Regular={len(regular_data)}, Paginated total={paginated_data['total']} ✓")
    
    def test_customers_total_matches_regular_endpoint(self, auth_headers):
        """Verify total count in paginated matches regular customers list"""
        # Get all customers (non-paginated)
        regular_response = requests.get(CUSTOMERS_URL, headers=auth_headers)
        assert regular_response.status_code == 200
        regular_data = regular_response.json()
        
        # Get paginated customers
        paginated_response = requests.get(CUSTOMERS_PAGINATED_URL, headers=auth_headers)
        assert paginated_response.status_code == 200
        paginated_data = paginated_response.json()
        
        # Total should match
        assert paginated_data["total"] == len(regular_data), \
            f"Paginated total ({paginated_data['total']}) should match regular endpoint count ({len(regular_data)})"
        
        print(f"Customers consistency: Regular={len(regular_data)}, Paginated total={paginated_data['total']} ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
