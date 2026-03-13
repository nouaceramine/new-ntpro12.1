# NT Commerce - منصة محاسبة ذكية مدعومة بالذكاء الاصطناعي

## نظرة عامة
NT Commerce هي منصة محاسبة سحابية احترافية مدعومة بالذكاء الاصطناعي. تجمع بين إدارة نقاط البيع، التحليلات المالية المتقدمة، والتكامل البنكي.

## المعمارية التقنية

### قاعدة البيانات: `ntbass` (MongoDB)
- المجموعات: accounts, agent_tasks, ai_chat_history, ai_insights, audit_logs, cash_boxes, chat_sessions, currencies, currency_rate_history, users, subscriptions, payments, invoices, products, inventory, sales, expenses, reports, system_logs, error_logs, saas_tenants, saas_plans, tax_rates, settings, bank_accounts, bank_transactions, bank_reconciliations, push_notifications, notification_preferences, whatsapp_config, whatsapp_messages

### Backend (FastAPI)
```
/app/backend/
├── server.py (~11,700 سطر - Legacy monolith)
├── routes/
│   ├── ai/chat_routes.py           # AI Chat & Insights
│   ├── accounting/accounting_routes.py  # Full Accounting
│   ├── saas_routes.py              # SaaS Management
│   ├── whatsapp_routes.py          # WhatsApp Business (MOCKED)
│   ├── tax_routes.py               # Tax Reports & Declarations
│   ├── currency_routes.py          # Multi-Currency
│   ├── notification_routes.py      # Push Notifications
│   ├── performance_routes.py       # Performance Monitoring
│   ├── banking_routes.py           # Bank Integration
│   ├── settings_routes.py          # Date/Time Settings
│   └── route_registry.py          # API Structure Documentation
├── utils/auth_helpers.py           # Shared Auth Functions
└── models/schemas.py               # Pydantic Models
```

### Frontend (React + Tailwind + Shadcn)
```
/app/frontend/
├── public/
│   ├── manifest.json               # PWA Manifest
│   └── service-worker.js           # Service Worker (Offline + Push)
└── src/
    ├── pages/
    │   ├── SmartDashboardPage.js    # AI Dashboard
    │   ├── AIChatPage.js            # AI Chat
    │   ├── AIAgentsPage.js          # 8 AI Agents
    │   ├── TaxReportsPage.js        # Tax Reports
    │   ├── WhatsAppPage.js          # WhatsApp Integration
    │   ├── CurrenciesPage.js        # Multi-Currency
    │   ├── BankingPage.js           # Bank Integration
    │   └── DateTimeSettingsPage.js  # Settings
    ├── components/
    │   ├── NotificationBell.js      # Notification Bell UI
    │   └── Layout.js                # Main Layout + Sidebar
    └── utils/globalDateFormatter.js # YYYY-MM-DD Format
```

## الميزات المنجزة (الكل)

### البنية التحتية
- [x] قاعدة بيانات `ntbass` مع 30+ مجموعة
- [x] نظام SaaS متعدد المستأجرين
- [x] 60+ فهرس لقاعدة البيانات
- [x] CORS لـ nt-commerce.net
- [x] JWT مـوحد عبر جميع الملفات

### الذكاء الاصطناعي
- [x] لوحة تحكم ذكية مع مؤشر الصحة المالية
- [x] محادثة AI مع GPT-4o
- [x] 8 وكلاء ذكاء اصطناعي

### المحاسبة
- [x] دليل حسابات، قيود، فواتير، مدفوعات

### التقارير الضريبية
- [x] TVA, IRG, TAP مع حسابات تلقائية
- [x] تصريحات ضريبية + ملخص سنوي

### العملات المتعددة
- [x] 10 عملات + محول تفاعلي

### WhatsApp Business
- [x] بنية كاملة + webhook + أوامر محاسبية (MOCKED)

### الإشعارات
- [x] API كامل + NotificationBell في الـ header
- [x] تفضيلات لكل مستخدم

### التكامل البنكي
- [x] حسابات بنكية (CRUD) + عمليات إيداع/سحب
- [x] مطابقة بنكية + سجل العمليات

### PWA (Progressive Web App)
- [x] manifest.json للتثبيت على الهاتف
- [x] Service Worker للعمل بدون إنترنت + Push

### الأداء
- [x] Performance timing middleware + كاش
- [x] X-Response-Time headers

### تنسيق التاريخ
- [x] YYYY-MM-DD بأرقام غربية في كامل النظام

## بيانات الاختبار
- **مدير عام**: admin@ntcommerce.com / Admin@2024
- **مستأجر**: ncr@ntcommerce.com / Test@123

## المهام المتبقية (Backlog)

### P1
- [ ] تقسيم server.py إلى modules أصغر (بدأ بـ route_registry.py)

### P2
- [ ] ربط WhatsApp مع Meta API الحقيقي
- [ ] إشعارات push فعلية عبر Service Worker

### P3
- [ ] استيراد بيانات Access
- [ ] تكامل بنكي حقيقي مع API بنوك جزائرية

---
*آخر تحديث: 13 مارس 2026*
*الإصدار: 4.0 - Full Featured + PWA + Banking*
