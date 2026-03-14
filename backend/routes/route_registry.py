"""
Route Registry - Documents the full API structure
NT Commerce 12.0 - Legendary Build
"""

# ===== EXTRACTED MODULES (New Architecture) =====
EXTRACTED_ROUTES = {
    # AI & Analysis
    "routes/ai/chat_routes.py": "AI Chat, Insights, Agents, Financial Analysis",
    "routes/accounting/accounting_routes.py": "Chart of Accounts, Journal Entries, Invoices, Payments",

    # Core Commerce
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

    # Legendary Build - New Systems
    "routes/repair_routes.py": "Repair Tickets, Spare Parts, Technicians (16 collections)",
    "routes/printing_routes.py": "Print Templates, Settings, Logs (5 collections)",
    "routes/defective_routes.py": "Defective Goods, Inspections, Returns, Disposals (11 collections)",
    "routes/backup_routes.py": "Backup Create/Restore, Schedules (5 collections)",
    "routes/security_routes.py": "Security Logs, Blocked IPs, API Keys, Sessions (9 collections)",
    "routes/wallet_routes.py": "Wallets, Transactions, Transfers",
    "routes/supplier_tracking_routes.py": "Supplier Goods, Orders, Best Price",
    "routes/search_routes.py": "Global Search, Suggestions, History",
    "routes/task_chat_routes.py": "Task Management, Internal Chat, Comments",
}

# ===== LEGACY IN SERVER.PY (Core Business Logic) =====
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
    "Defective Products (L11108-11390)": "Track, Manage (Legacy)",
}

# ===== API ROUTE MAP =====
API_ENDPOINTS = {
    # Repair System
    "POST /api/repairs/tickets": "Create repair ticket",
    "GET /api/repairs/tickets": "List repair tickets",
    "GET /api/repairs/tickets/{id}": "Get ticket with parts & history",
    "PUT /api/repairs/tickets/{id}": "Update ticket (status, diagnosis)",
    "DELETE /api/repairs/tickets/{id}": "Delete ticket",
    "GET /api/repairs/stats": "Repair statistics",
    "POST /api/repairs/parts": "Add spare part",
    "GET /api/repairs/parts": "List spare parts",
    "POST /api/repairs/tickets/{id}/use-part": "Use part in repair",
    "POST /api/repairs/technicians": "Add technician",
    "GET /api/repairs/technicians": "List technicians",

    # Defective Goods
    "GET /api/defective/categories": "Defect categories",
    "POST /api/defective/goods": "Report defective item",
    "GET /api/defective/goods": "List defective items",
    "POST /api/defective/inspections": "Create inspection",
    "POST /api/defective/returns": "Create supplier return",
    "GET /api/defective/returns": "List returns",
    "POST /api/defective/disposals": "Create disposal record",
    "GET /api/defective/stats": "Defective stats",

    # Printing & Barcode
    "POST /api/printing/templates": "Create print template",
    "GET /api/printing/templates": "List templates",
    "GET /api/printing/settings": "Get printer settings",
    "PUT /api/printing/settings": "Update printer settings",
    "POST /api/printing/log": "Log print action",
    "POST /api/barcodes/scan": "Scan barcode",
    "POST /api/barcodes/labels": "Create label design",

    # Backup System
    "POST /api/backup/create": "Create backup",
    "GET /api/backup/list": "List backups",
    "POST /api/backup/schedules": "Create backup schedule",
    "GET /api/backup/stats/summary": "Backup statistics",

    # Security
    "GET /api/security/logs": "Security event logs",
    "GET /api/security/logs/stats": "Security statistics",
    "GET /api/security/blocked-ips": "Blocked IPs list",
    "POST /api/security/blocked-ips": "Block IP address",
    "GET /api/security/audit-logs": "Audit trail",
    "POST /api/security/api-keys": "Create API key",
    "GET /api/security/sessions": "Active sessions",

    # Wallet
    "GET /api/wallet": "Get wallet balance",
    "POST /api/wallet/add-funds": "Deposit funds",
    "POST /api/wallet/deduct": "Withdraw funds",
    "POST /api/wallet/transfer": "Transfer between wallets",
    "GET /api/wallet/transactions": "Transaction history",
    "GET /api/wallet/stats": "Wallet statistics",

    # Supplier Tracking
    "POST /api/supplier-tracking/goods": "Link product to supplier",
    "GET /api/supplier-tracking/goods/best-price/{id}": "Compare supplier prices",
    "POST /api/supplier-tracking/orders": "Create supplier order",
    "GET /api/supplier-tracking/stats": "Supplier stats",

    # Search
    "GET /api/search/global?q=": "Global search",
    "GET /api/search/suggestions": "Search suggestions",
    "GET /api/search/history": "Search history",

    # Tasks & Chat
    "POST /api/tasks": "Create task",
    "GET /api/tasks": "List tasks",
    "POST /api/tasks/{id}/comments": "Add comment",
    "POST /api/chat/rooms": "Create chat room",
    "GET /api/chat/rooms": "List chat rooms",
    "POST /api/chat/rooms/{id}/messages": "Send message",
}
