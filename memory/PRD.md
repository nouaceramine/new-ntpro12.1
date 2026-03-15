# NT Commerce 12.0 - Legendary Build PRD

## Original Problem Statement
Build "NT Commerce" Legendary Version - SaaS platform with 152 collections, 11 AI robots, multi-tenancy, RBAC permissions, external integrations, and PWA support. Now implementing "NT Commerce 12.0" upgrade with security fixes, performance improvements, and new features.

## Tech Stack
- **Frontend**: React + Shadcn/UI + Tailwind CSS (RTL Arabic) + PWA
- **Backend**: FastAPI + MongoDB (Motor async) + slowapi (rate limiting)
- **AI**: OpenAI GPT-4o via Emergent LLM Key
- **Scheduling**: APScheduler (11 robots)
- **Auth**: JWT + bcrypt + TOTP (2FA) + RBAC + slowapi rate limiting
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
├── main.py                # ~1,160 lines (orchestrator)
├── config/                # database.py, settings.py
├── utils/                 # auth.py, permissions.py, dependencies.py
├── models/                # 152 Pydantic models
├── robots/                # 11 AI robots
├── routes/                # 65 modular route files
│   ├── auth_users_routes.py (rate-limited + permission-protected)
│   ├── products_routes.py (permission-protected)
│   ├── sales_routes.py (permission-protected)
│   ├── ... (11 permission-protected files)
│   ├── stripe_routes.py (LIVE)
│   ├── sendgrid_integration_routes.py (ready for key)
│   ├── whatsapp_integration_routes.py (ready for key)
│   ├── yalidine_integration_routes.py (ready for key)
│   ├── push_notification_routes.py
│   └── ... (65 total)
└── frontend/
    ├── public/manifest.json (PWA)
    ├── public/service-worker.js (offline + push)
    └── src/pages/IntegrationStatusPage.jsx
```

### External Integration APIs
| Integration | Status | Env Variable | Endpoints |
|-------------|--------|-------------|-----------|
| Stripe | LIVE (test key) | STRIPE_API_KEY | /api/payments/* |
| SendGrid | Ready | SENDGRID_API_KEY | /api/integrations/email/* |
| WhatsApp | Ready | WHATSAPP_API_TOKEN, WHATSAPP_PHONE_NUMBER_ID | /api/integrations/whatsapp/* |
| Yalidine | Ready | YALIDINE_API_ID, YALIDINE_API_TOKEN | /api/integrations/yalidine/* |
| Push | Ready | VAPID_PRIVATE_KEY, VAPID_EMAIL | /api/push/* |

### Security Configuration
| Feature | Status | Details |
|---------|--------|---------|
| CORS | SECURED | Origins from CORS_ORIGINS env var, no wildcard fallback |
| Password Logging | FIXED | No password data in logs |
| Rate Limiting | ACTIVE | slowapi: 20/min login, 10/min register |
| JWT Secret | SECURED | JWT_SECRET_KEY from .env, no hardcoded fallback |
| Admin Permissions | ENHANCED | Identity + active status checks |
| Brute Force | ACTIVE | 5 attempts then 15 min lockout |

### Permission System
- 73 permission-protected endpoints across 11 route files
- Admin roles bypass all checks
- `utils/permissions.py`: `require_permission("module.action")`

---

## Completed Tasks
- [x] P0: main.py entry point migration
- [x] P0: 65 modular route files
- [x] P1: Permission system (73 endpoints)
- [x] P2: Stripe integration (LIVE with test key)
- [x] P2: SendGrid integration (ready for key)
- [x] P2: WhatsApp Business API (ready for key)
- [x] P2: Yalidine shipping (ready for key)
- [x] P2: PWA (manifest + service worker)
- [x] P2: Push Notifications backend
- [x] P2: Integration Status Dashboard page
- [x] **P0 Security: CORS hardened (specific origins, no wildcard)**
- [x] **P0 Security: Password logging removed**
- [x] **P0 Security: Rate limiting via slowapi**
- [x] **P0 Security: JWT secret moved to .env**
- [x] **P0 Security: Admin permissions enhanced**

## Remaining Backlog

### P1 - Performance Improvements (NEXT)
- [ ] Solve N+1 Query Problem (MongoDB $lookup aggregations)
- [ ] Add Pagination to all list endpoints
- [ ] Enforce Stronger Password policies (validate_password utility)
- [ ] Implement Redis Caching (CacheManager service)

### P2 - New Features
- [ ] Implement Repair System (/api/repairs - already has routes, needs testing)
- [ ] Implement Wallet System (/api/wallet - already has routes, needs testing)
- [ ] Implement Backup System (/api/backup - already has routes, needs testing)
- [ ] Implement AI Robots (inventory + profit analysis enhancements)

### P3
- [ ] Full multi-tenancy agent hierarchy
- [ ] Worker mobile app
- [ ] Docker deployment
- [ ] Data import/export tools

---

## Test Results
| Iter | Backend | Frontend | Notes |
|------|---------|----------|-------|
| 71 | 25/25 | 100% | main.py migration |
| 72 | 30/32 | 100% | Legacy routes extraction |
| 73 | 35/35 | 100% | 8 route files + permission system |
| 74 | 23/23 | 100% | P2 integrations |
| 75 | 17/17 | - | P0 Security fixes (CORS, rate limit, JWT, password, admin) |

## Credentials
- **Super Admin**: admin@ntcommerce.com / Admin@2024
- **Tenant**: ncr@ntcommerce.com / Test@123
- **Normal User**: test@test.com / Test@123
- **DB**: ntbass

*Last updated: 2026-03-15*
*Version: 12.0 - NT Commerce 12.0 Phase 1 (P0 Security Fixes Complete)*
