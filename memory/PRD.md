# NT Commerce - منصة محاسبة ذكية مدعومة بالذكاء الاصطناعي

## نظرة عامة
NT Commerce هي منصة محاسبة سحابية احترافية مدعومة بالذكاء الاصطناعي، تجمع بين إدارة نقاط البيع والتحليلات المالية المتقدمة.

## المتطلبات الأصلية
- نظام SaaS متعدد المستأجرين
- إدارة المبيعات والمخزون والعملاء
- تحليلات مالية ذكية مدعومة بـ GPT-4o
- 8 وكلاء ذكاء اصطناعي للأتمتة المحاسبية
- تكامل WhatsApp Business API
- تقارير ضريبية متقدمة
- دعم عملات متعددة
- نظام إشعارات متقدم
- تحسين الأداء

## المعمارية التقنية

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py                           # الخادم الرئيسي (~11,700 سطر)
├── routes/
│   ├── ai/chat_routes.py              # محادثة AI ورؤى
│   ├── accounting/accounting_routes.py # قيود، فواتير، دفعات
│   ├── saas_routes.py                 # إدارة SaaS
│   ├── whatsapp_routes.py             # تكامل WhatsApp Business
│   ├── tax_routes.py                  # التقارير الضريبية
│   ├── currency_routes.py             # العملات المتعددة
│   ├── notification_routes.py         # الإشعارات
│   ├── performance_routes.py          # مراقبة الأداء
│   └── settings_routes.py            # إعدادات التاريخ/الوقت
├── services/ai/
│   ├── llm_service.py                # خدمة LLM (GPT-4o)
│   └── agents.py                     # 8 وكلاء ذكيين
├── utils/
│   └── auth_helpers.py               # دوال المصادقة المشتركة
└── models/
    ├── accounting/schemas.py          # نماذج المحاسبة
    └── ai/schemas.py                 # نماذج AI
```

### Frontend (React + Tailwind + Shadcn)
```
/app/frontend/src/
├── pages/
│   ├── SmartDashboardPage.js          # لوحة التحكم الذكية
│   ├── AIChatPage.js                  # المحاسب الذكي
│   ├── AIAgentsPage.js                # وكلاء AI
│   ├── TaxReportsPage.js             # التقارير الضريبية
│   ├── WhatsAppPage.js               # تكامل WhatsApp
│   ├── CurrenciesPage.js             # العملات المتعددة
│   ├── DateTimeSettingsPage.js        # إعدادات التاريخ
│   └── admin/SaasAdminPage.js        # إدارة SaaS
├── contexts/
│   └── DateFormatContext.js           # تنسيق التاريخ العالمي
├── utils/
│   └── globalDateFormatter.js         # تنسيق YYYY-MM-DD
└── components/
    └── ui/                           # مكونات Shadcn
```

## الميزات المنجزة

### المرحلة 1: البنية التحتية
- [x] إعادة هيكلة الـ routes
- [x] إضافة 60+ فهرس لقاعدة البيانات
- [x] نماذج المحاسبة Pydantic
- [x] خدمات AI منفصلة

### المرحلة 2: لوحة التحكم الذكية
- [x] مؤشر الصحة المالية (0-100)
- [x] إحصائيات الإيرادات/المصروفات/الأرباح
- [x] رسم بياني تطور الإيرادات
- [x] رؤى AI تلقائية

### المرحلة 3: المحاسب الذكي - AI Chat
- [x] محادثة طبيعية مع GPT-4o
- [x] أسئلة مقترحة
- [x] حفظ سجل المحادثات

### المرحلة 4: وكلاء AI الـ 8
- [x] معالج الفواتير، مصنف المصروفات، المحلل المالي
- [x] كاشف الاحتيال، مولد التقارير، مساعد الضرائب
- [x] المتنبئ، الأتمتة اليومية

### المرحلة 5: المحاسبة
- [x] دليل الحسابات، القيود اليومية، الفواتير
- [x] المدفوعات، المصروفات، التقارير المالية

### المرحلة 6: تكامل WhatsApp Business (11 مارس 2026)
- [x] صفحة إدارة WhatsApp كاملة
- [x] إعدادات API (Phone Number ID, Access Token, Verify Token)
- [x] Webhook endpoint للاستقبال والإرسال
- [x] 5 أوامر محاسبية: مصروف، فاتورة، رصيد، تقرير، مبيعات
- [x] سجل الرسائل الواردة والصادرة
- [x] إحصائيات الرسائل

### المرحلة 7: التقارير الضريبية المتقدمة (11 مارس 2026)
- [x] 5 معدلات ضريبية افتراضية (TVA, IRG, TAP, اقتطاع)
- [x] إنشاء تقارير ضريبية بحساب TVA وضريبة الدخل و TAP
- [x] التصريحات الضريبية (مسودة/مقدم/مدفوع)
- [x] ملخص سنوي مع تفاصيل ربع سنوية
- [x] إدارة معدلات الضرائب (CRUD)

### المرحلة 8: العملات المتعددة (11 مارس 2026)
- [x] 10 عملات مدعومة (DZD, USD, EUR, GBP, SAR, AED, TRY, MAD, TND, CNY)
- [x] محول عملات تفاعلي
- [x] تعديل أسعار الصرف
- [x] بطاقات تحويل سريع

### المرحلة 9: نظام الإشعارات (11 مارس 2026)
- [x] API إشعارات كامل (CRUD)
- [x] عداد الإشعارات غير المقروءة
- [x] تفضيلات الإشعارات لكل مستخدم
- [x] دعم Browser Push API

### المرحلة 10: تحسين الأداء (11 مارس 2026)
- [x] Middleware لقياس زمن الاستجابة
- [x] نظام كاش في الذاكرة مع TTL
- [x] API مراقبة الأداء وإحصائيات DB
- [x] Headers X-Response-Time

### المرحلة 11: إصلاح تنسيق التاريخ (11 مارس 2026)
- [x] تنسيق YYYY-MM-DD في كامل النظام
- [x] إصلاح جميع ملفات admin (SaasAdminPage, AgentsDashboard, SystemAlerts, Monitoring)
- [x] إصلاح مكونات (DatabaseManager, DefectiveProducts, AIAssistant, ExportPrintButtons)
- [x] أرقام غربية في جميع التواريخ

## واجهات API

### AI APIs
```
POST /api/ai/chat, GET /api/ai/agents/status, POST /api/ai/agents/run
GET /api/ai/financial-health, GET /api/ai/insights, GET /api/ai/forecast/{type}
GET /api/ai/daily-summary, POST /api/ai/classify-expense
```

### Accounting APIs
```
GET/POST /api/accounting/accounts, /journal-entries, /invoices, /payments, /expenses
GET /api/accounting/reports/profit-loss, /balance-sheet, /cash-flow, /audit-log
```

### Tax APIs
```
GET/POST /api/tax/rates, PUT/DELETE /api/tax/rates/{id}
GET /api/tax/report?start_date=&end_date=, GET /api/tax/summary/{year}
GET/POST /api/tax/declarations, PUT /api/tax/declarations/{id}/status
```

### WhatsApp APIs
```
GET/PUT /api/whatsapp/config, POST /api/whatsapp/send
GET/POST /api/whatsapp/webhook, GET /api/whatsapp/messages, /stats
```

### Currency APIs
```
GET /api/currencies/, PUT /api/currencies/rates
POST /api/currencies/convert, GET/PUT /api/currencies/settings
GET /api/currencies/rate-history/{code}
```

### Notification APIs
```
GET/POST /api/notifications/, PUT /api/notifications/{id}/read
PUT /api/notifications/read-all, GET /api/notifications/unread-count
GET/PUT /api/notifications/preferences, POST /api/notifications/subscribe
```

### Performance APIs
```
GET /api/performance/stats, POST /api/performance/clear-cache
GET /api/performance/db-stats
```

## بيانات الاختبار
- **مدير عام**: admin@ntcommerce.com / Admin@2024
- **مستأجر**: ncr@ntcommerce.com / Test@123

## المهام القادمة (Backlog)

### P1 - أولوية عالية
- [ ] تقسيم server.py إلى ملفات أصغر (بدأ بـ auth_helpers.py)
- [ ] تحسين أداء الصفحات الكبيرة (lazy loading, virtualization)

### P2 - أولوية متوسطة
- [ ] استيراد بيانات من ملفات Access
- [ ] إشعارات push للمتصفح (Service Worker)
- [ ] ربط WhatsApp مع Meta API الحقيقي

### P3 - مستقبلي
- [ ] تطبيق موبايل (PWA)
- [ ] تكامل بنكي
- [ ] عملات متعددة في الفواتير

## التكاملات
- **OpenAI GPT-4o**: عبر Emergent LLM Key
- **MongoDB**: قاعدة البيانات
- **Stripe**: المدفوعات
- **SendGrid**: البريد الإلكتروني
- **WhatsApp Business API**: تكامل مهيأ (MOCKED - يحتاج مفاتيح Meta)

---
*آخر تحديث: 11 مارس 2026*
*الإصدار: 3.0 - Full Featured AI Platform*
