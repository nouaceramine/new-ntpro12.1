# NT Commerce 12.0 - Legendary Build PRD

## Original Problem Statement
Build "NT Commerce" Legendary Version - an all-encompassing SaaS platform that merges features from nt-pro, current NT Commerce, and extensive new functionalities. 152 database collections, 11 AI robots, complete repair system, defective goods management, multi-tenancy, and advanced analytics.

## User Personas
- **Super Admin**: Full system access, manages tenants, plans, global settings
- **Tenant Admin**: Manages their store - products, sales, customers, employees
- **Seller/Employee**: POS access, daily sessions, basic operations
- **Agent**: Regional agent with commission-based hierarchy

## Core Requirements
- Arabic UI (RTL) with French support
- Dark theme design
- Multi-tenant SaaS architecture
- 152 MongoDB collections defined via Pydantic models
- 11 AI background robots
- Complete CRUD for all business entities
- Real-time dashboard analytics

## Tech Stack
- **Frontend**: React + Shadcn/UI + Tailwind CSS
- **Backend**: FastAPI + MongoDB (Motor async)
- **AI**: OpenAI GPT-4o via Emergent LLM Key
- **Scheduling**: APScheduler for robot tasks
- **Auth**: JWT + bcrypt + TOTP (2FA)

---

## What's Been Implemented

### Phase 1-3 (Previous Sessions)
- Full auth system (login, register, JWT, 2FA)
- Products CRUD with barcode/SKU generation
- Customers & Suppliers CRUD
- Sales & Purchases with invoicing
- Cash box management (4 default boxes)
- Employee management with accounts, attendance, advances
- Expense tracking
- Debt management (receivable + payable)
- Warehouse management with stock transfers
- Loyalty program
- Notification system
- PDF report generation (ReportLab)
- 11 AI robots (Inventory, Sales, Customer, Report, Pricing, Maintenance, Profit, Repair, Prediction, Notification, Supplier)
- Dashboard with real-time stats, charts, analytics
- POS (Point of Sale) page
- Daily session management

### Phase 4 (2026-03-14 - Current Session)
- **SmartNotificationsPage**: Fixed missing route in App.js, added sidebar link
- **Major Refactoring - Route Extraction from server.py (12K lines)**:
  - `/app/backend/routes/products_routes.py` - Products CRUD, pagination, quick search, barcode gen (~320 lines)
  - `/app/backend/routes/customers_routes.py` - Customers CRUD, pagination, code gen (~170 lines)
  - `/app/backend/routes/sales_routes.py` - Sales CRUD, pagination, returns, code gen (~180 lines)
  - `/app/backend/routes/purchases_routes.py` - Purchases CRUD, debt management, code gen (~170 lines)
  - `/app/backend/routes/stats_routes.py` - Dashboard stats, sales analytics, profit reports, AI predictions (~280 lines)
  - Total: ~1,120 lines of clean, modular business logic
- **Testing**: Backend 100% (25/25), Frontend 100% - All pages verified

### All Frontend Pages (Status)
| Page | Route | Status |
|------|-------|--------|
| Dashboard | / | LIVE |
| POS | /pos | LIVE |
| Products | /products | LIVE |
| Customers | /customers | LIVE |
| Suppliers | /suppliers | LIVE |
| Sales History | /sales | LIVE |
| Purchases | /purchases | LIVE |
| Expenses | /expenses | LIVE |
| Cash Boxes | /cash-boxes | LIVE |
| Debts | /debts | LIVE |
| Employees | /employees | LIVE |
| Warehouses | /warehouses | LIVE |
| Notifications | /notifications | LIVE |
| Smart Notifications | /smart-notifications | LIVE |
| AI Agents | /ai-agents | LIVE |
| Reports | /reports | LIVE |
| Analytics | /analytics | LIVE |
| Settings | /settings | LIVE |
| Repairs | /repair-reception | LIVE |
| Defective Goods | /defective-goods | LIVE |
| Backup System | /backup-system | LIVE |
| Wallet | /wallet-management | LIVE |
| Task Management | /task-management | LIVE |
| Internal Chat | /internal-chat | LIVE |
| Permissions | /permissions | LIVE |
| Security Dashboard | /security-dashboard | LIVE |
| 2FA Setup | /2fa | LIVE |

### Backend Route Files (Extracted)
| File | Prefix | Status |
|------|--------|--------|
| products_routes.py | /products | LIVE |
| customers_routes.py | /customers | LIVE |
| sales_routes.py | /sales | LIVE |
| purchases_routes.py | /purchases | LIVE |
| stats_routes.py | /stats,/dashboard,/analytics,/reports | LIVE |
| repair_routes.py | /repairs | LIVE |
| defective_routes.py | /defective | LIVE |
| backup_routes.py | /backup | LIVE |
| wallet_routes.py | /wallet | LIVE |
| task_routes.py | /tasks | LIVE |
| chat_routes.py | /chat | LIVE |
| supplier_tracking_routes.py | /supplier-tracking | LIVE |
| security_routes.py | /security | LIVE |
| permissions_routes.py | /permissions | LIVE |
| smart_notifications_routes.py | /smart-notifications | LIVE |

---

## Prioritized Backlog

### P0 - Critical
- [ ] Continue server.py refactoring (still 12K lines, old code coexists with extracted routes)
- [ ] Remove dead code from server.py (sections now in extracted route files)
- [ ] Create config/ directory (database.py, settings.py)

### P1 - High Priority
- [ ] Implement remaining business logic in Employee routes extraction
- [ ] Extract Expenses, Cash Box, Warehouse, Debt sections from server.py
- [ ] Create main.py entry point (as specified in Legendary Prompt)
- [ ] Full permissions enforcement (500+ permissions across all routes)

### P2 - Medium Priority
- [ ] Stripe payment integration
- [ ] Yalidine shipping integration
- [ ] WhatsApp Meta API integration
- [ ] PWA support + Push notifications
- [ ] Email notifications (SendGrid/Resend)

### P3 - Lower Priority
- [ ] Full multi-tenancy business logic (agent hierarchy, commissions)
- [ ] Worker mobile app
- [ ] Social media features
- [ ] Advanced barcode/printing system
- [ ] Docker deployment setup
- [ ] Data import/export tools

---

## Test Credentials
- **Super Admin**: admin@ntcommerce.com / Admin@2024
- **Tenant**: ncr@ntcommerce.com / Test@123
- **Database**: ntbass

## Test Reports
- iteration_66.json: SmartNotifications route fix verified
- iteration_67.json: Route extraction verified (25/25 backend, 100% frontend)

*Last updated: 2026-03-14*
*Version: 12.0 - Legendary Build Phase 4*
