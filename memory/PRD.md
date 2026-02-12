# NT Commerce - Multi-Tenant SaaS Platform

## Original Problem Statement
Multi-tenant SaaS e-commerce platform (FastAPI + React + MongoDB) with:
- Each tenant's data fully isolated in their own database
- Super Admin manages platform (tenants, plans, agents)
- Tenant role manages their own store
- Unified login page for all user types

## Architecture
- **Backend**: FastAPI (Python) - monolithic `server.py` (~10,800 lines) with `api_router`
- **Frontend**: React.js with Arabic RTL support
- **Database**: MongoDB with database-per-tenant isolation pattern
- **Auth**: JWT with `tenant_id` claim for tenant users

### Data Isolation Pattern (ContextVar + DB Proxy)
```
Request → Middleware extracts tenant_id from JWT → Sets ContextVar → 
DB Proxy routes all `db.*` calls to tenant-specific database automatically
```
- `main_db`: Always points to the SaaS management database (plans, tenants, agents)
- `db` (proxy): Routes to tenant DB when ContextVar is set, falls back to main_db otherwise
- Middleware: Runs on every request, extracts `tenant_id` from JWT Bearer token

### Key Files
- `/app/backend/server.py`: Main application (all routes, models, middleware)
- `/app/backend/config/database.py`: DB config (unused - logic is in server.py)
- `/app/backend/routes/`: Modular routes (written but NOT connected to app)
- `/app/frontend/src/pages/UnifiedLoginPage.js`: Single login page
- `/app/frontend/src/contexts/AuthContext.js`: Auth state management

## What's Been Implemented

### Completed (Feb 2026)
- ✅ **Critical Fix: Tenant Data Isolation** - ContextVar + DB Proxy pattern
  - All tenant data (products, customers, sales, etc.) fully isolated
  - 22/22 backend isolation tests passed
  - Super Admin sees only main_db data, not tenant data
- ✅ **Automatic DB Creation** on first tenant login
- ✅ **Unified Login Page** - single `/portal` for all user types
- ✅ **Backend Modular Structure** - routes/, models/, services/, config/ directories created
- ✅ **Super Admin UI Cleanup** - tenant-specific menus hidden for super admin
- ✅ **RBAC Dependencies** - `get_tenant_admin`, `require_tenant` created for API-level access control
- ✅ **Dashboard Fix** - TenantResponse optional fields resolved

### Test Credentials
- Super Admin: `super@ntcommerce.com` / `password`
- Tenant A: `tenanta@test.com` / `password123`
- Tenant B: `tenantb@test.com` / `password123`

## Prioritized Backlog

### P1: Apply RBAC to Routes
- `get_tenant_admin` and `require_tenant` dependencies exist but aren't applied to routes yet
- Critical routes (products, customers, sales) should use these instead of `get_admin_user`
- This prevents Super Admin from accidentally creating data in main_db

### P1: Modular Routes Migration
- `/app/backend/routes/` has well-written, tenant-aware route files (customers, sales, purchases, etc.)
- These are NOT connected to the app (only `api_router` from `server.py` is active)
- Plan: Gradually migrate routes from monolithic `server.py` to modular files
- Risk: High - server.py has 10,800+ lines with complex interdependencies

### P2: Code Cleanup
- Remove dead code in server.py that's duplicated in routes/
- Clean up unused imports and models
- Standardize error messages (Arabic vs English)

### P2: Enhanced Testing
- Add automated regression tests for all CRUD operations per tenant
- Add frontend E2E tests for tenant login and data operations
