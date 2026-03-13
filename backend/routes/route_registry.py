"""
Route Registry - Documents the full API structure
Shows what's in server.py (legacy) vs extracted modules
"""

# ===== EXTRACTED MODULES (New Architecture) =====
EXTRACTED_ROUTES = {
    "routes/ai/chat_routes.py": "AI Chat, Insights, Agents, Financial Analysis",
    "routes/accounting/accounting_routes.py": "Chart of Accounts, Journal Entries, Invoices, Payments",
    "routes/saas_routes.py": "SaaS Management, Plans, Tenants, Stats",
    "routes/settings_routes.py": "Date/Time Settings, Formatting",
    "routes/whatsapp_routes.py": "WhatsApp Business API Integration",
    "routes/tax_routes.py": "Tax Reports, Rates, Declarations",
    "routes/notification_routes.py": "Push Notifications, Preferences",
    "routes/currency_routes.py": "Multi-Currency, Exchange Rates",
    "routes/performance_routes.py": "Performance Monitoring, Caching",
    "routes/banking_routes.py": "Bank Accounts, Transactions, Reconciliation",
    "routes/database_routes.py": "Database Management",
    "routes/system_errors.py": "System Error Tracking",
}

# ===== LEGACY IN SERVER.PY (To be extracted in future) =====
LEGACY_ROUTES = {
    "Auth (L704-915)": "Login, Register, Token, Password Reset",
    "Products (L1021-1440)": "CRUD, Search, Barcode, Categories",
    "Customers (L1782-2020)": "CRUD, Blacklist, Debt Reminders",
    "Sales (L2586-2826)": "Create Sale, Returns, History",
    "Purchases (L2827-3028)": "Purchase Orders, Receiving",
    "Cash Box (L3029-3186)": "Open/Close, Transactions",
    "Stats & Reports (L3308-3736)": "Dashboard Stats, Charts",
    "Employees (L3894-4238)": "CRUD, Attendance, Alerts",
    "Debts (L4239-4363)": "Customer/Supplier Debts",
    "Suppliers (L2328-2585)": "CRUD, Advance Payments",
    "Warehouse (L2173-2276)": "Multi-warehouse, Transfers",
    "Inventory (L2277-2327)": "Inventory Sessions",
    "Loyalty (L6133-6283)": "Points, Rewards",
    "Online Store (L10884-11107)": "Public Store, Cart",
    "Defective Products (L11108-11390)": "Track, Manage",
}
