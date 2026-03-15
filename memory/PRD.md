# NT Commerce 12.0 - Legendary Build PRD

## Original Problem Statement
Build "NT Commerce" Legendary Version - SaaS platform with 152 collections, 11 AI robots, multi-tenancy, RBAC permissions, external integrations, and PWA support. Implementing "NT Commerce 12.0" upgrade with security fixes, performance improvements, and new features.

## Tech Stack
- **Frontend**: React + Shadcn/UI + Tailwind CSS (RTL Arabic) + PWA
- **Backend**: FastAPI + MongoDB (Motor async) + slowapi + Redis
- **AI**: OpenAI GPT-4o via Emergent LLM Key
- **Scheduling**: APScheduler (11 robots)
- **Auth**: JWT + bcrypt + TOTP (2FA) + RBAC + slowapi rate limiting + strong password policy
- **Cache**: Redis (localhost:6379)
- **Payments**: Stripe (test key active)

---

## Architecture

### File Structure
```
/app/backend/
├── server.py              # 6 lines (supervisor entry)
├── main.py                # orchestrator + cache routes
├── utils/                 # pagination.py, password_validator.py
├── models/                # 152 Pydantic models
├── robots/                # 11 AI robots (inventory, debt, report, customer, pricing, maintenance, profit, repair, prediction, notification, supplier)
├── services/              # cache_service.py, notification_service.py, etc.
├── routes/                # 65 modular route files
```

---

## Completed Tasks (All Phases)

### P0 - Security (COMPLETE)
- [x] CORS hardened (specific origins, no wildcard)
- [x] Password logging removed
- [x] Rate limiting via slowapi (20/min login, 10/min register)
- [x] JWT secret moved to .env
- [x] Admin permissions enhanced

### P1 - Performance (COMPLETE)
- [x] N+1 fix (batch fetch in customers & suppliers)
- [x] Pagination (9 endpoints: products, sales, purchases, expenses, debts, suppliers, employees, customers, cashbox)
- [x] Strong password validation on register + update
- [x] Redis cache (stats dashboard 60s TTL, admin management API)

### P2 - Features (COMPLETE)
- [x] Repair System verified: ticket CRUD, status tracking, history, pagination, stats
- [x] Wallet System verified: auto-create, add/deduct funds, transactions pagination, admin wallet list
- [x] Backup System enhanced: create, download (real file), restore from backup, list, stats
- [x] AI Robots enhanced: profit_robot fixed (retail_price), all 11 robots running

## Remaining Backlog

### P3
- [ ] Full multi-tenancy agent hierarchy
- [ ] Worker mobile app
- [ ] Docker deployment
- [ ] Data import/export tools

---

## Test Results
| Iter | Pass Rate | Notes |
|------|-----------|-------|
| 75 | 17/17 | P0 Security fixes |
| 76 | 28/28 | P1 Performance improvements |
| 77 | 24/24 | P2 Features (repairs, wallet, backup, robots) |

## Credentials
- **Super Admin**: admin@ntcommerce.com / Admin@2024
- **Tenant**: ncr@ntcommerce.com / Test@123
- **DB**: ntbass

*Last updated: 2026-03-15*
*Version: 12.0 - P0+P1+P2 Complete*
