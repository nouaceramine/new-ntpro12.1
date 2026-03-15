# NT Commerce 12.0 - Legendary Build PRD

## Original Problem Statement
Build "NT Commerce" Legendary Version - all-encompassing SaaS platform with 152 database collections, 11 AI robots, repair system, defective goods management, multi-tenancy, and advanced analytics.

## Tech Stack
- **Frontend**: React + Shadcn/UI + Tailwind CSS (RTL Arabic)
- **Backend**: FastAPI + MongoDB (Motor async)
- **AI**: OpenAI GPT-4o via Emergent LLM Key
- **Scheduling**: APScheduler (11 robots)
- **Auth**: JWT + bcrypt + TOTP (2FA) + RBAC permissions

---

## Architecture (Final State)

### File Structure
```
/app/backend/
├── server.py          # 6 lines - thin wrapper (supervisor entry point)
├── main.py            # 1,150 lines - app orchestrator
├── config/
│   ├── database.py    # DB connections, tenant management
│   └── settings.py    # App settings
├── utils/
│   ├── auth.py        # Authentication utilities
│   ├── permissions.py # Permission enforcement (require_permission factory)
│   ├── dependencies.py
│   ├── errors.py
│   └── pagination.py
├── models/            # 152 Pydantic models
├── robots/            # 11 AI robots
├── routes/            # 61 modular route files
│   ├── auth_users_routes.py
│   ├── products_routes.py (permission-protected)
│   ├── sales_routes.py (permission-protected)
│   ├── customers_routes.py (permission-protected)
│   ├── purchases_routes.py (permission-protected)
│   ├── expenses_routes.py (permission-protected)
│   ├── employees_routes.py (permission-protected)
│   ├── debts_routes.py (permission-protected)
│   ├── cashbox_routes.py (permission-protected)
│   ├── daily_sessions_routes.py (permission-protected)
│   ├── suppliers_core_routes.py (permission-protected)
│   ├── warehouse_core_routes.py (permission-protected)
│   ├── online_store_routes.py
│   ├── sendgrid_email_routes.py
│   ├── sms_marketing_routes.py
│   ├── stripe_routes.py
│   ├── utility_routes.py
│   ├── notifications_routes.py
│   ├── ocr_invoice_routes.py
│   ├── recharge_sim_routes.py
│   ├── shipping_loyalty_routes.py
│   ├── families_permissions_routes.py
│   ├── system_sync_routes.py
│   └── ... (61 total)
└── frontend/
    └── ... (27+ pages)
```

### Permission System
- **utils/permissions.py**: `create_permission_checker(db, get_current_user)` factory
- **require_permission()**: Dependency for route-level access control
- Admin roles (admin, tenant_admin, super_admin, manager, owner) bypass all checks
- Non-admin users checked against role permissions from `db.roles`
- 73 permission-protected endpoints across 11 route files
- Permission format: `module.action` (e.g., `products.create`, `sales.view`)

---

## Test Results History
| Iteration | Backend | Frontend | Notes |
|-----------|---------|----------|-------|
| 67 | 25/25 (100%) | 100% | First 5 modules extracted |
| 68 | 32/32 (100%) | 100% | 9 modules verified |
| 69 | 34/34 (100%) | 100% | 3,735 line removal |
| 70 | 27/27 (100%) | 100% | 16 modules, 42% reduction |
| 71 | 25/25 (100%) | 100% | main.py migration |
| 72 | 30/32 (93.75%) | 100% | Legacy routes extraction |
| 73 | 35/35 (100%) | 100% | 8 new route files + permission system, 0 regressions |

---

## Completed P0/P1 Tasks
- [x] Create main.py entry point
- [x] Extract ALL inline routes from server.py/main.py
- [x] server.py: 12,099 → 6 lines (thin wrapper)
- [x] main.py: 7,076 → 1,150 lines (orchestrator only)
- [x] 61 modular route files
- [x] Permission system (utils/permissions.py)
- [x] 73 permission-protected endpoints
- [x] ObjectId serialization fixes
- [x] 8 new route files from legacy split

## Prioritized Backlog

### P2 - Medium Priority
- [ ] Stripe payment integration (real keys)
- [ ] Yalidine shipping integration
- [ ] WhatsApp Meta API integration
- [ ] SendGrid real integration
- [ ] PWA support + Push notifications

### P3 - Lower Priority
- [ ] Full multi-tenancy agent hierarchy
- [ ] Worker mobile app
- [ ] Docker deployment setup
- [ ] Data import/export tools

---

## Test Credentials
- **Super Admin**: admin@ntcommerce.com / Admin@2024
- **Tenant**: ncr@ntcommerce.com / Test@123
- **Database**: ntbass

*Last updated: 2026-03-15*
*Version: 12.0 - Legendary Build Phase 6 Complete (Full Modular Architecture + Permissions)*
