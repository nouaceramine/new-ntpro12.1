# NT Commerce - منصة محاسبة ذكية مدعومة بالذكاء الاصطناعي

## نظرة عامة
NT Commerce هي منصة محاسبة سحابية احترافية مدعومة بالذكاء الاصطناعي. تجمع بين إدارة نقاط البيع، التحليلات المالية المتقدمة، والتكامل البنكي.

## المعمارية التقنية

### قاعدة البيانات: `ntbass` (MongoDB)
- المجموعات: accounts, agent_tasks, ai_chat_history, ai_insights, audit_logs, cash_boxes, chat_sessions, currencies, currency_rate_history, users, subscriptions, payments, invoices, products, inventory, sales, expenses, reports, system_logs, error_logs, saas_tenants, saas_plans, tax_rates, settings, bank_accounts, bank_transactions, bank_reconciliations, push_notifications, notification_preferences, whatsapp_config, whatsapp_messages, auto_reports, report_pdfs, collection_reports, reorder_recommendations, stockout_predictions, debt_reminders, sms_log

### Backend (FastAPI)
```
/app/backend/
├── server.py (~11,800 سطر)
├── robots/
│   ├── __init__.py
│   ├── robot_manager.py        # مدير الروبوتات المركزي
│   ├── inventory_robot.py      # روبوت المخزون (ML predictions)
│   ├── debt_robot.py           # روبوت الديون والتحصيل
│   └── report_robot.py         # روبوت التقارير (PDF + Email)
├── services/
│   ├── notification_service.py # خدمة الإشعارات
│   ├── sms_service.py          # خدمة SMS (MOCKED)
│   ├── email_service.py        # خدمة البريد (SendGrid)
│   └── emergent_wrapper.py
├── routes/
│   ├── ai/chat_routes.py
│   ├── accounting/accounting_routes.py
│   ├── saas_routes.py
│   ├── whatsapp_routes.py       # (MOCKED)
│   ├── tax_routes.py
│   ├── currency_routes.py
│   ├── notification_routes.py
│   ├── performance_routes.py
│   ├── banking_routes.py
│   ├── settings_routes.py
│   └── route_registry.py
├── utils/
│   ├── auth_helpers.py
│   ├── errors.py
│   └── pagination.py
├── models/schemas.py
├── tests/
│   ├── test_robots.py
│   ├── test_robots_comprehensive.py
│   ├── test_auth.py
│   └── ... (30+ test files)
├── docs/
│   ├── README.md
│   └── CONTRIBUTING.md
└── config/database.py
```

### Frontend (React + Tailwind + Shadcn)
```
/app/frontend/src/
├── pages/
│   ├── SmartDashboardPage.js
│   ├── AIChatPage.js
│   ├── AIAgentsPage.js
│   ├── TaxReportsPage.js
│   ├── WhatsAppPage.js
│   ├── CurrenciesPage.js
│   ├── BankingPage.js
│   └── DateTimeSettingsPage.js
├── components/
│   ├── NotificationBell.js
│   └── Layout.js
└── utils/globalDateFormatter.js
```

## الميزات المنجزة

### الروبوتات الذكية (جديد - مارس 2026)
- [x] روبوت المخزون - مراقبة، توصيات إعادة طلب، توقع نفاد (ML)
- [x] روبوت الديون - متابعة، تذكيرات، تحليل أداء التحصيل
- [x] روبوت التقارير - يومي/أسبوعي/شهري + PDF + بريد إلكتروني
- [x] مدير الروبوتات المركزي (RobotManager)
- [x] API endpoints: status, run, restart, stop-all, start-all
- [x] خدمات مساعدة: NotificationService, SMSService(MOCKED), EmailService
- [x] تشغيل تلقائي عند بدء الخادم

### البنية التحتية
- [x] قاعدة بيانات `ntbass` مع 30+ مجموعة
- [x] نظام SaaS متعدد المستأجرين
- [x] 60+ فهرس لقاعدة البيانات
- [x] CORS لـ nt-commerce.net
- [x] JWT موحد عبر جميع الملفات
- [x] Rate Limiting (120 طلب/دقيقة)

### الذكاء الاصطناعي
- [x] لوحة تحكم ذكية مع مؤشر الصحة المالية
- [x] محادثة AI مع GPT-4o
- [x] 8 وكلاء ذكاء اصطناعي

### المحاسبة
- [x] دليل حسابات، قيود، فواتير، مدفوعات

### التقارير الضريبية
- [x] TVA, IRG, TAP مع حسابات تلقائية

### العملات المتعددة
- [x] 10 عملات + محول تفاعلي

### WhatsApp Business
- [x] بنية كاملة + webhook (MOCKED)

### الإشعارات
- [x] API كامل + NotificationBell

### التكامل البنكي
- [x] حسابات بنكية + عمليات + مطابقة

### PWA
- [x] manifest.json + Service Worker

## بيانات الاختبار
- **مدير عام**: admin@ntcommerce.com / Admin@2024
- **مستأجر**: ncr@ntcommerce.com / Test@123

## المهام المتبقية (Backlog)

### P1
- [ ] واجهة أمامية (Frontend) لعرض حالة الروبوتات والتقارير
- [ ] تقسيم server.py إلى modules أصغر

### P2
- [ ] ربط WhatsApp مع Meta API الحقيقي
- [ ] ربط SMS مع مزود حقيقي (Twilio)
- [ ] إشعارات push فعلية عبر Service Worker
- [ ] حماية متقدمة (2FA, brute-force protection)

### P3
- [ ] روبوتات إضافية (العملاء، التسعير، الصيانة)
- [ ] استيراد بيانات Access
- [ ] تكامل بنكي حقيقي مع API بنوك جزائرية

---
*آخر تحديث: 13 مارس 2026*
*الإصدار: 5.0 - Intelligent Robots + Full Featured*
