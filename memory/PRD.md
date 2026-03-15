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
- **Email**: SendGrid (ready for API key)
- **Messaging**: WhatsApp Business API (ready for API key)
- **Shipping**: Yalidine (ready for API key)
- **Push**: Web Push Notifications (ready for VAPID key)

---

## Architecture

### File Structure
```
/app/backend/
├── server.py              # 6 lines (supervisor entry)
├── main.py                # ~1,160 lines (orchestrator + cache routes)
├── config/                # database.py, settings.py
├── utils/                 # auth.py, permissions.py, pagination.py, password_validator.py
├── models/                # 152 Pydantic models
├── robots/                # 11 AI robots
├── services/              # cache_service.py, notification_service.py, etc.
├── routes/                # 65 modular route files (all with pagination)
└── frontend/
    └── src/pages/
```

### Security Configuration (P0 - COMPLETE)
| Feature | Status | Details |
|---------|--------|---------|
| CORS | SECURED | Origins from CORS_ORIGINS env var, no wildcard fallback |
| Password Logging | FIXED | No password data in logs |
| Rate Limiting | ACTIVE | slowapi: 20/min login, 10/min register |
| JWT Secret | SECURED | JWT_SECRET_KEY from .env, no hardcoded fallback |
| Admin Permissions | ENHANCED | Identity + active status checks |
| Brute Force | ACTIVE | 5 attempts then 15 min lockout |
| Password Policy | ENFORCED | Min 8 chars, uppercase, lowercase, digit, special char |

### Performance Configuration (P1 - COMPLETE)
| Feature | Status | Details |
|---------|--------|---------|
| N+1 Fix | DONE | Batch fetch in customers & suppliers |
| Pagination | DONE | 9 endpoints: products, sales, purchases, expenses, debts, suppliers, employees, customers, cashbox transactions |
| Password Validation | DONE | Strong rules on register + password update |
| Redis Cache | ACTIVE | Stats dashboard cached 60s, admin management API |

---

## Completed Tasks
- [x] P0: main.py entry point migration
- [x] P0: 65 modular route files
- [x] P1: Permission system (73 endpoints)
- [x] P2: Stripe integration (LIVE with test key)
- [x] P2: SendGrid/WhatsApp/Yalidine integrations (ready for keys)
- [x] P2: PWA + Push Notifications
- [x] **P0 Security: CORS, password logging, rate limiting, JWT secret, admin permissions**
- [x] **P1 Performance: N+1 fix, pagination (9 endpoints), password validation, Redis cache**

## Remaining Backlog

### P2 - New Features (NEXT)
- [ ] Verify/test Repair System (/api/repairs - routes exist)
- [ ] Verify/test Wallet System (/api/wallet - routes exist)
- [ ] Verify/test Backup System (/api/backup - routes exist)
- [ ] Enhance AI Robots (inventory + profit analysis)

### P3
- [ ] Full multi-tenancy agent hierarchy
- [ ] Worker mobile app
- [ ] Docker deployment
- [ ] Data import/export tools

---

## Test Results
| Iter | Backend | Notes |
|------|---------|-------|
| 73 | 35/35 | Route files + permission system |
| 74 | 23/23 | P2 integrations |
| 75 | 17/17 | P0 Security fixes |
| 76 | 28/28 | P1 Performance improvements |

## Credentials
- **Super Admin**: admin@ntcommerce.com / Admin@2024
- **Tenant**: ncr@ntcommerce.com / Test@123
- **Normal User**: test@test.com / Test@123
- **DB**: ntbass

*Last updated: 2026-03-15*
*Version: 12.0 - Phase 2 Complete (P0 Security + P1 Performance)*
