# NT Commerce 12.0 - Legendary Build PRD

## Original Problem Statement
Build "NT Commerce" Legendary Version - all-encompassing SaaS platform merging features from nt-pro, current NT Commerce, and extensive new functionalities. 152 database collections, 11 AI robots, complete repair system, defective goods management, multi-tenancy, and advanced analytics.

## User Personas
- **Super Admin**: Full system access, manages tenants, plans, global settings
- **Tenant Admin**: Manages their store - products, sales, customers, employees
- **Seller/Employee**: POS access, daily sessions, basic operations
- **Agent**: Regional agent with commission-based hierarchy

## Tech Stack
- **Frontend**: React + Shadcn/UI + Tailwind CSS
- **Backend**: FastAPI + MongoDB (Motor async)
- **AI**: OpenAI GPT-4o via Emergent LLM Key
- **Scheduling**: APScheduler for robot tasks
- **Auth**: JWT + bcrypt + TOTP (2FA)

---

## What's Been Implemented

### Backend Architecture (30 Modular Route Files)
| Route File | Prefix | Lines | Status |
|-----------|--------|-------|--------|
| products_routes.py | /products | 379 | LIVE |
| customers_routes.py | /customers | 165 | LIVE |
| sales_routes.py | /sales | 214 | LIVE |
| purchases_routes.py | /purchases | 194 | LIVE |
| stats_routes.py | /stats,/dashboard,/analytics,/reports | 371 | LIVE |
| employees_routes.py | /employees | 201 | LIVE |
| cashbox_routes.py | /cash-boxes,/transactions | 71 | LIVE |
| debts_routes.py | /debts | 79 | LIVE |
| expenses_routes.py | /expenses | 126 | LIVE |
| repair_routes.py | /repairs | 214 | LIVE |
| defective_routes.py | /defective | 264 | LIVE |
| backup_routes.py | /backup | 146 | LIVE |
| wallet_routes.py | /wallet | 182 | LIVE |
| task_chat_routes.py | /tasks,/chat | 157 | LIVE |
| permissions_routes.py | /permissions | 365 | LIVE |
| smart_notifications_routes.py | /smart-notifications | 70 | LIVE |
| security_routes.py | /security | 179 | LIVE |
| saas_routes.py | /saas | 1117 | LIVE |
| + 12 more utility routes | various | ~2500 | LIVE |
| **Total** | | **6,954** | |

### Frontend Pages (27+ Pages)
All pages connected to live APIs with Arabic RTL support:
Dashboard, POS, Products, Customers, Suppliers, Sales, Purchases, Expenses, Cash Boxes, Debts, Employees, Warehouses, Notifications, Smart Notifications, AI Agents, Reports, Analytics, Settings, Repairs, Defective Goods, Backup, Wallet, Tasks, Chat, Permissions, Security, 2FA

### Infrastructure
- 152 Pydantic models in `/app/backend/models/`
- 11 AI robots running on APScheduler
- config/ directory with database.py and settings.py
- Full JWT auth with 2FA (TOTP) support
- Multi-tenant database isolation

---

## Prioritized Backlog

### P0 - Critical
- [ ] Remove dead/shadowed code from server.py (routes now in modular files)
- [ ] Create main.py entry point with lifespan manager

### P1 - High Priority
- [ ] Extract remaining sections from server.py (Daily Sessions, Warehouses, Suppliers, etc.)
- [ ] Full permissions enforcement across all routes
- [ ] Complete tenant onboarding flow

### P2 - Medium Priority
- [ ] Stripe payment integration
- [ ] Yalidine shipping integration
- [ ] WhatsApp Meta API integration
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

## Test Reports
- iteration_67: Route extraction verified (25/25 backend)
- iteration_68: All 9 modules verified (32/32 backend, 100% frontend)

*Last updated: 2026-03-14*
*Version: 12.0 - Legendary Build Phase 4*
