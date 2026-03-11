# NT Commerce - منصة محاسبة ذكية مدعومة بالذكاء الاصطناعي

## نظرة عامة
NT Commerce هي منصة محاسبة سحابية احترافية مدعومة بالذكاء الاصطناعي، تجمع بين إدارة نقاط البيع والتحليلات المالية المتقدمة.

## المتطلبات الأصلية
- نظام SaaS متعدد المستأجرين
- إدارة المبيعات والمخزون والعملاء
- تحليلات مالية ذكية مدعومة بـ GPT-4o
- 8 وكلاء ذكاء اصطناعي للأتمتة المحاسبية
- تكامل WhatsApp Business API (مخطط)

## المعمارية التقنية

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py                    # الخادم الرئيسي (~11,650 سطر)
├── routes/
│   ├── ai/                      # مسارات الذكاء الاصطناعي
│   │   └── chat_routes.py       # محادثة AI ورؤى
│   ├── accounting/              # مسارات المحاسبة
│   │   └── accounting_routes.py # قيود، فواتير، دفعات
│   └── saas_routes.py          # إدارة SaaS
├── services/
│   └── ai/
│       ├── llm_service.py      # خدمة LLM (GPT-4o)
│       └── agents.py           # 8 وكلاء ذكيين
└── models/
    ├── accounting/schemas.py   # نماذج المحاسبة
    └── ai/schemas.py           # نماذج AI
```

### Frontend (React + Tailwind)
```
/app/frontend/src/
├── pages/
│   ├── SmartDashboardPage.js   # لوحة التحكم الذكية
│   ├── AIChatPage.js           # المحاسب الذكي
│   └── AIAgentsPage.js         # وكلاء AI
└── components/
    └── ui/                     # مكونات Shadcn
```

## الميزات المنجزة ✅

### المرحلة 1: البنية التحتية (مكتملة)
- [x] إعادة هيكلة الـ routes
- [x] إضافة 60+ فهرس لقاعدة البيانات
- [x] نماذج المحاسبة Pydantic
- [x] خدمات AI منفصلة

### المرحلة 2: لوحة التحكم الذكية (مكتملة)
- [x] مؤشر الصحة المالية (0-100)
- [x] إحصائيات الإيرادات/المصروفات/الأرباح
- [x] رسم بياني تطور الإيرادات
- [x] رؤى AI تلقائية
- [x] ملخص يومي

### المرحلة 3: المحاسب الذكي - AI Chat (مكتملة)
- [x] محادثة طبيعية مع GPT-4o
- [x] أسئلة مقترحة
- [x] حفظ سجل المحادثات
- [x] اقتراحات متابعة

### المرحلة 4: وكلاء AI (مكتملة)
- [x] معالج الفواتير (Invoice Processor)
- [x] مصنف المصروفات (Expense Classifier)
- [x] المحلل المالي (Financial Analyzer)
- [x] كاشف الاحتيال (Fraud Detector)
- [x] مولد التقارير (Smart Reporter)
- [x] مساعد الضرائب (Tax Assistant)
- [x] المتنبئ (Forecaster)
- [x] الأتمتة اليومية (Daily Automation)

### المرحلة 5: المحاسبة (مكتملة)
- [x] دليل الحسابات
- [x] القيود اليومية
- [x] الفواتير
- [x] المدفوعات
- [x] المصروفات
- [x] تقارير مالية (P&L, Balance Sheet, Cash Flow)
- [x] سجل التدقيق

## واجهات API الجديدة

### AI APIs
```
POST /api/ai/chat              # محادثة مع المحاسب الذكي
GET  /api/ai/agents/status     # حالة الوكلاء الـ 8
POST /api/ai/agents/run        # تشغيل وكيل
GET  /api/ai/financial-health  # مؤشر الصحة المالية
GET  /api/ai/insights          # رؤى AI
GET  /api/ai/forecast/{type}   # تنبؤات
GET  /api/ai/daily-summary     # ملخص يومي
POST /api/ai/classify-expense  # تصنيف مصروف
```

### Accounting APIs
```
GET/POST /api/accounting/accounts        # دليل الحسابات
GET/POST /api/accounting/journal-entries # القيود
GET/POST /api/accounting/invoices        # الفواتير
GET/POST /api/accounting/payments        # المدفوعات
GET/POST /api/accounting/expenses        # المصروفات
GET /api/accounting/reports/profit-loss  # تقرير P&L
GET /api/accounting/reports/balance-sheet # الميزانية
GET /api/accounting/reports/cash-flow    # التدفق النقدي
GET /api/accounting/audit-log           # سجل التدقيق
```

## بيانات الاختبار
- **مدير عام**: admin@ntcommerce.com / Admin@2024
- **مستأجر**: ncr@ntcommerce.com / Test@123

## المهام القادمة (Backlog)

### P1 - أولوية عالية
- [ ] تقسيم server.py إلى ملفات أصغر
- [ ] تكامل WhatsApp Business API
- [ ] تحسين أداء الصفحات الكبيرة

### P2 - أولوية متوسطة
- [ ] استيراد بيانات من ملفات Access
- [ ] تقارير ضريبية متقدمة
- [ ] إشعارات push

### P3 - مستقبلي
- [ ] تطبيق موبايل
- [ ] تكامل بنكي
- [ ] عملات متعددة

## التكاملات
- **OpenAI GPT-4o**: عبر Emergent LLM Key
- **MongoDB**: قاعدة البيانات
- **Stripe**: المدفوعات
- **SendGrid**: البريد الإلكتروني

---
*آخر تحديث: 11 مارس 2026*
*الإصدار: 2.0 - AI-Powered*
