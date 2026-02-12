# NT Commerce - Multi-Tenant SaaS Platform

## Original Problem Statement
Multi-tenant SaaS e-commerce platform (FastAPI + React + MongoDB) with:
- Each tenant's data fully isolated in their own database
- Super Admin manages platform (tenants, plans, agents)
- Tenant role manages their own store
- Unified login page for all user types

## Architecture
- **Backend**: FastAPI (Python) - `server.py` with `api_router` (336 routes)
- **Frontend**: React.js with Arabic RTL support, Shadcn UI components
- **Database**: MongoDB with database-per-tenant isolation pattern
- **Auth**: JWT with `tenant_id` claim for tenant users

### Data Isolation Pattern (ContextVar + DB Proxy)
```
Request → Middleware extracts tenant_id from JWT → Sets ContextVar →
DB Proxy routes all `db.*` calls to tenant-specific database automatically
```
- `main_db`: Always points to the SaaS management database
- `db` (proxy): Routes to tenant DB when ContextVar is set, falls back to main_db
- Database naming: `tenant_{id_with_underscores}` (hyphens replaced)

### RBAC Architecture
- `get_tenant_admin`: Requires tenant_id in JWT - for tenant write operations (251 routes)
- `require_tenant`: Requires tenant_id in JWT - for tenant read operations
- `get_admin_user`: Allows super_admin + admin - for user management only
- `get_super_admin`: Requires super_admin role - for SaaS management routes

### Key Files
- `/app/backend/server.py`: Main application (all routes, models, middleware)
- `/app/frontend/src/pages/admin/SaasAdminPage.js`: SaaS Admin with monitoring
- `/app/frontend/src/pages/UnifiedLoginPage.js`: Single login page
- `/app/frontend/src/contexts/AuthContext.js`: Auth state management

## What's Been Implemented

### Phase 1 - Foundation (Completed)
- Automatic DB creation on first tenant login
- Unified login page (`/portal`) for all user types
- Backend modular structure created (routes/, models/, services/)
- Super Admin UI cleanup (tenant-specific menus hidden)
- Dashboard TenantResponse optional fields fix

### Phase 2 - Security (Feb 12, 2026 - Completed)
- **Critical Fix: Tenant Data Isolation** - ContextVar + DB Proxy pattern
  - 22/22 backend isolation tests passed
- **RBAC on 251 routes** - Super Admin blocked from tenant data
  - 18/18 RBAC tests passed
- **Monitoring Dashboard** for Super Admin
  - Per-tenant stats: products, customers, sales, revenue, last activity
  - Summary cards with totals
  - Sortable table with all tenant metrics

### Test Credentials
- Super Admin: `super@ntcommerce.com` / `password`
- Tenant A: `tenanta@test.com` / `password123`
- Tenant B: `tenantb@test.com` / `password123`

## Remaining Backlog

### P2: Code Cleanup
- `/app/backend/routes/` has unused modular route stubs (not connected to app)
- server.py could be migrated to modular structure in the future
- Standardize error messages (Arabic vs English)

### P2: E2E Frontend Tests
- Playwright tests for tenant login → products → data isolation flow
- Super Admin monitoring dashboard tests
