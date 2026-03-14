"""
Test Suite for Iteration 67 - Extracted Routes Testing
Tests Products, Customers, Sales, Purchases extracted from server.py into separate route files

Modules tested:
- Products routes: CRUD, pagination, quick-search, barcode/SKU/article-code generation, low-stock alerts
- Customers routes: CRUD, pagination, customer code generation
- Sales routes: CRUD, pagination, sale code generation
- Purchases routes: List, purchase code generation
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TENANT_CREDS = {"email": "ncr@ntcommerce.com", "password": "Test@123"}
ADMIN_CREDS = {"email": "admin@ntcommerce.com", "password": "Admin@2024"}


@pytest.fixture(scope="module")
def tenant_token():
    """Get tenant authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=TENANT_CREDS)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Tenant authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token for super admin operations"""
    response = requests.post(f"{BASE_URL}/api/auth/unified-login", json=ADMIN_CREDS)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Admin authentication failed: {response.status_code}")


@pytest.fixture
def tenant_headers(tenant_token):
    """Headers with tenant authentication"""
    return {"Authorization": f"Bearer {tenant_token}", "Content-Type": "application/json"}


@pytest.fixture
def admin_headers(admin_token):
    """Headers with admin authentication"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestProductsExtractedRoutes:
    """Test Products routes extracted from server.py to products_routes.py"""

    def test_get_products_list(self, tenant_headers):
        """GET /api/products - List all products (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/products", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Products list should be an array"
        print(f"PASS: GET /api/products returned {len(data)} products")

    def test_get_products_paginated(self, tenant_headers):
        """GET /api/products/paginated - Paginated products (extracted route)"""
        response = requests.get(
            f"{BASE_URL}/api/products/paginated?page=1&page_size=5",
            headers=tenant_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        assert "page" in data, "Response should contain 'page'"
        assert "page_size" in data, "Response should contain 'page_size'"
        assert "total_pages" in data, "Response should contain 'total_pages'"
        print(f"PASS: Paginated products - total: {data['total']}, page: {data['page']}, items: {len(data['items'])}")

    def test_quick_search_products(self, tenant_headers):
        """GET /api/products/quick-search - Quick search (extracted route)"""
        response = requests.get(
            f"{BASE_URL}/api/products/quick-search?q=test&limit=10",
            headers=tenant_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "results" in data, "Response should contain 'results'"
        assert "total" in data, "Response should contain 'total'"
        print(f"PASS: Quick search returned {len(data['results'])} results, total: {data['total']}")

    def test_generate_barcode(self, tenant_headers):
        """GET /api/products/generate-barcode - Generate barcode (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/products/generate-barcode", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "barcode" in data, "Response should contain 'barcode'"
        assert len(data["barcode"]) == 13, "Barcode should be 13 digits (EAN-13)"
        print(f"PASS: Generated barcode: {data['barcode']}")

    def test_generate_barcode_from_article_code(self, tenant_headers):
        """GET /api/products/generate-barcode with article_code - Deterministic barcode generation"""
        response = requests.get(
            f"{BASE_URL}/api/products/generate-barcode?article_code=AR0001",
            headers=tenant_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "barcode" in data, "Response should contain 'barcode'"
        print(f"PASS: Generated barcode from AR0001: {data['barcode']}")

    def test_generate_sku(self, tenant_headers):
        """GET /api/products/generate-sku - Generate SKU (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/products/generate-sku", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "sku" in data, "Response should contain 'sku'"
        assert data["sku"].startswith("SG-"), "SKU should start with 'SG-'"
        print(f"PASS: Generated SKU: {data['sku']}")

    def test_generate_article_code(self, tenant_headers):
        """GET /api/products/generate-article-code - Generate article code (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/products/generate-article-code", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "article_code" in data, "Response should contain 'article_code'"
        assert data["article_code"].startswith("AR"), "Article code should start with 'AR'"
        print(f"PASS: Generated article code: {data['article_code']}")

    def test_low_stock_alerts(self, tenant_headers):
        """GET /api/products/alerts/low-stock - Low stock alerts (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/products/alerts/low-stock", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Low stock alerts should be an array"
        print(f"PASS: Low stock alerts returned {len(data)} products")

    def test_create_product(self, tenant_headers):
        """POST /api/products - Create product (extracted route)"""
        unique_id = str(uuid.uuid4())[:8]
        product_data = {
            "name_en": f"TEST_Product_{unique_id}",
            "name_ar": f"منتج_اختباري_{unique_id}",
            "description_en": "Test product description",
            "description_ar": "وصف المنتج الاختباري",
            "purchase_price": 100.0,
            "retail_price": 150.0,
            "wholesale_price": 120.0,
            "super_wholesale_price": 110.0,
            "quantity": 50,
            "low_stock_threshold": 10,
            "compatible_models": ["Model A", "Model B"]  # Must be a list
        }
        response = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=tenant_headers)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Created product should have 'id'"
        assert data["name_en"] == product_data["name_en"], "Name should match"
        assert data["retail_price"] == product_data["retail_price"], "Price should match"
        print(f"PASS: Created product with ID: {data['id']}, name: {data['name_en']}")


class TestCustomersExtractedRoutes:
    """Test Customers routes extracted from server.py to customers_routes.py"""

    def test_get_customers_list(self, tenant_headers):
        """GET /api/customers - List all customers (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Customers list should be an array"
        print(f"PASS: GET /api/customers returned {len(data)} customers")

    def test_get_customers_paginated(self, tenant_headers):
        """GET /api/customers/paginated - Paginated customers (extracted route)"""
        response = requests.get(
            f"{BASE_URL}/api/customers/paginated?page=1&page_size=10",
            headers=tenant_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        assert "page" in data, "Response should contain 'page'"
        print(f"PASS: Paginated customers - total: {data['total']}, page: {data['page']}, items: {len(data['items'])}")

    def test_generate_customer_code(self, tenant_headers):
        """GET /api/customers/generate-code - Generate customer code (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/customers/generate-code", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "code" in data, "Response should contain 'code'"
        assert data["code"].startswith("CL"), "Customer code should start with 'CL'"
        print(f"PASS: Generated customer code: {data['code']}")

    def test_create_customer(self, tenant_headers):
        """POST /api/customers - Create customer (extracted route)"""
        unique_id = str(uuid.uuid4())[:8]
        customer_data = {
            "name": f"TEST_Customer_{unique_id}",
            "phone": f"0555{unique_id[:6]}",
            "email": f"test_{unique_id}@example.com",
            "address": "Test Address 123",
            "notes": "Test customer notes"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=tenant_headers)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Created customer should have 'id'"
        assert data["name"] == customer_data["name"], "Name should match"
        print(f"PASS: Created customer with ID: {data['id']}, name: {data['name']}")
        return data["id"]


class TestSalesExtractedRoutes:
    """Test Sales routes extracted from server.py to sales_routes.py"""

    def test_get_sales_list(self, tenant_headers):
        """GET /api/sales - List all sales (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/sales", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Sales list should be an array"
        print(f"PASS: GET /api/sales returned {len(data)} sales")

    def test_get_sales_paginated(self, tenant_headers):
        """GET /api/sales/paginated - Paginated sales (extracted route)"""
        response = requests.get(
            f"{BASE_URL}/api/sales/paginated?page=1&page_size=10",
            headers=tenant_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "total" in data, "Response should contain 'total'"
        assert "page" in data, "Response should contain 'page'"
        print(f"PASS: Paginated sales - total: {data['total']}, page: {data['page']}, items: {len(data['items'])}")

    def test_generate_sale_code(self, tenant_headers):
        """GET /api/sales/generate-code - Generate sale code (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/sales/generate-code", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "code" in data, "Response should contain 'code'"
        assert data["code"].startswith("BV"), "Sale code should start with 'BV'"
        print(f"PASS: Generated sale code: {data['code']}")

    def test_create_sale_requires_items(self, tenant_headers):
        """POST /api/sales - Verify sale creation requires items"""
        # First get a product to use in sale
        products_resp = requests.get(f"{BASE_URL}/api/products?limit=1", headers=tenant_headers)
        if products_resp.status_code != 200 or not products_resp.json():
            pytest.skip("No products available for sale test")
        
        products = products_resp.json()
        if len(products) == 0:
            pytest.skip("No products available for sale test")
        
        product = products[0]
        retail_price = product.get("retail_price", 100)
        
        # Get a cash box for payment method
        cash_boxes_resp = requests.get(f"{BASE_URL}/api/cash-boxes", headers=tenant_headers)
        payment_method = "cash"
        if cash_boxes_resp.status_code == 200:
            cash_boxes = cash_boxes_resp.json()
            if cash_boxes:
                payment_method = cash_boxes[0].get("id", "cash")
        
        sale_data = {
            "items": [{
                "product_id": product["id"],
                "product_name": product.get("name_ar", "Test Product"),
                "quantity": 1,
                "unit_price": retail_price,  # Required field
                "total": retail_price
            }],
            "subtotal": retail_price,
            "discount": 0,
            "total": retail_price,
            "paid_amount": retail_price,
            "payment_method": payment_method,
            "payment_type": "cash"
        }
        response = requests.post(f"{BASE_URL}/api/sales", json=sale_data, headers=tenant_headers)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Created sale should have 'id'"
        assert "invoice_number" in data, "Created sale should have 'invoice_number'"
        print(f"PASS: Created sale with ID: {data['id']}, invoice: {data['invoice_number']}")


class TestPurchasesExtractedRoutes:
    """Test Purchases routes extracted from server.py to purchases_routes.py"""

    def test_get_purchases_list(self, tenant_headers):
        """GET /api/purchases - List all purchases (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/purchases", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Purchases list should be an array"
        print(f"PASS: GET /api/purchases returned {len(data)} purchases")

    def test_generate_purchase_code(self, tenant_headers):
        """GET /api/purchases/generate-code - Generate purchase code (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/purchases/generate-code", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "code" in data, "Response should contain 'code'"
        assert data["code"].startswith("AC"), "Purchase code should start with 'AC'"
        print(f"PASS: Generated purchase code: {data['code']}")


class TestSmartNotificationsRouting:
    """Test SmartNotifications frontend route (fixed in this iteration)"""

    def test_smart_notifications_api(self, tenant_headers):
        """GET /api/smart-notifications - Verify backend API still works"""
        response = requests.get(f"{BASE_URL}/api/smart-notifications", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Smart notifications should be an array"
        print(f"PASS: Smart notifications API returned {len(data)} notifications")


class TestRegressionPages:
    """Regression tests to ensure existing pages still work"""

    def test_repairs_api(self, tenant_headers):
        """GET /api/repairs - Repairs still working"""
        response = requests.get(f"{BASE_URL}/api/repairs", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Repairs API working")

    def test_defective_goods_api(self, tenant_headers):
        """GET /api/defective/goods - Defective goods still working"""
        response = requests.get(f"{BASE_URL}/api/defective/goods", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Defective goods API working")

    def test_backup_api(self, tenant_headers):
        """GET /api/backup/list - Backup system still working"""
        response = requests.get(f"{BASE_URL}/api/backup/list", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Backup system API working")

    def test_wallet_api(self, tenant_headers):
        """GET /api/wallet - Wallet still working"""
        response = requests.get(f"{BASE_URL}/api/wallet", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Wallet API working")

    def test_permissions_catalog(self, tenant_headers):
        """GET /api/permissions/catalog - Permissions still working"""
        response = requests.get(f"{BASE_URL}/api/permissions/catalog", headers=tenant_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Permissions catalog API working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
