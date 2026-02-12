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
- Middleware extracts `tenant_id` from JWT → Sets ContextVar → DB Proxy routes all `db.*` calls to tenant-specific database
- `main_db`: SaaS management database (plans, tenants, agents)
- `db` (proxy): Routes to tenant DB or falls back to main_db
- Database naming: `tenant_{id_with_underscores}`

### RBAC Architecture
- `get_tenant_admin`: Requires tenant_id - for tenant write operations (251 routes)
- `require_tenant`: Requires tenant_id - for tenant read operations
- `get_admin_user`: Allows super_admin + admin - for user management only
- `get_super_admin`: Requires super_admin - for SaaS management + impersonation

## What's Been Implemented

### Phase 1 - Foundation
- Automatic DB creation on first tenant login
- Unified login page (`/portal`) for all user types
- Backend modular structure created
- Super Admin UI cleanup
- Dashboard TenantResponse fix

### Phase 2 - Security (Feb 12, 2026)
- **Data Isolation** - ContextVar + DB Proxy (22/22 tests passed)
- **RBAC on 251 routes** (18/18 tests passed)

### Phase 3 - Admin Features (Feb 12, 2026)
- **Tenant Impersonation** - Super Admin can login to any tenant account via `POST /api/saas/impersonate/{tenant_id}` (6/6 tests)
- **Agent Name** in tenant table - shows which agent created the tenant account
- **Monitoring Dashboard** with:
  - Per-tenant stats: products, customers, sales, revenue, last activity
  - Summary cards with platform totals
  - **Automatic alerts**: expiring subscriptions (warning), expired subscriptions (critical), product/user limit reached (warning)
  - Sortable table + refresh
- All features tested: **14/14 tests passed (iteration 40)**

### Test Credentials
- Super Admin: `super@ntcommerce.com` / `password`
- Tenant A: `tenanta@test.com` / `password123`
- Tenant B: `tenantb@test.com` / `password123`

## Remaining Backlog
### P2: Code Cleanup
- `/app/backend/routes/` has unused modular route stubs
- server.py could be migrated to modular structure
### P2: E2E Frontend Tests
- Playwright tests for full user flows
