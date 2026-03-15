"""
NT Commerce 12.0 - Legendary Build
Main Entry Point with Lifespan Manager

This is the canonical entry point for the application.
It imports the app from server.py and will gradually replace it
as more routes are extracted into modular files.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

logger = logging.getLogger("nt-commerce")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # ── Startup ──
    logger.info("NT Commerce 12.0 - Legendary Build starting...")
    
    # Import and run startup tasks from server
    from server import (
        startup_db_client,
        robot_manager,
        client
    )
    
    await startup_db_client()
    logger.info("NT Commerce 12.0 - All systems operational")
    
    yield
    
    # ── Shutdown ──
    logger.info("NT Commerce 12.0 - Shutting down...")
    await robot_manager.stop_all()
    client.close()
    logger.info("NT Commerce 12.0 - Shutdown complete")


# Re-export the app from server.py
# This ensures backward compatibility while establishing main.py as the entry point
from server import app

# ── Route Registry ──
# All extracted modular routes are registered in server.py's legendary build section.
# As more routes are extracted, they can be registered here instead.
#
# Current modular route files (14 extracted):
# - routes/products_routes.py      -> /api/products
# - routes/customers_routes.py     -> /api/customers
# - routes/sales_routes.py         -> /api/sales
# - routes/purchases_routes.py     -> /api/purchases
# - routes/stats_routes.py         -> /api/stats, /api/dashboard, /api/analytics, /api/reports
# - routes/employees_routes.py     -> /api/employees
# - routes/cashbox_routes.py       -> /api/cash-boxes, /api/transactions
# - routes/debts_routes.py         -> /api/debts
# - routes/expenses_routes.py      -> /api/expenses
# - routes/daily_sessions_routes.py -> /api/daily-sessions
# - routes/suppliers_core_routes.py -> /api/suppliers
# - routes/warehouse_core_routes.py -> /api/warehouses, /api/stock-transfers, /api/inventory-sessions
# - routes/customer_debts_routes.py -> /api/customers/*/debt, /api/supplier-debts, /api/debts/summary
# - routes/repair_routes.py        -> /api/repairs
# - routes/defective_routes.py     -> /api/defective
# - routes/backup_routes.py        -> /api/backup
# - routes/wallet_routes.py        -> /api/wallet
# - routes/permissions_routes.py   -> /api/permissions
# - routes/smart_notifications_routes.py -> /api/smart-notifications
# - routes/security_routes.py      -> /api/security
#
# Legacy routes still in server.py:
# - Auth (login, register, 2FA)
# - Notifications CRUD
# - Product/Customer/Supplier Families
# - Price History
# - Invoice PDF Generation
# - API Keys Management
# - System Settings
# - Loyalty Program
# - SMS Marketing
# - WhatsApp Integration
# - Stripe Integration
# - Email Notifications
# - Online Store
# - Real-time Sync
# - Advanced Sales Tracking
# - Robot API Endpoints
