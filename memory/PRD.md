# NT Commerce - منصة محاسبة ذكية مدعومة بالذكاء الاصطناعي

## نظرة عامة
NT Commerce هي منصة محاسبة سحابية احترافية مدعومة بالذكاء الاصطناعي. تجمع بين إدارة نقاط البيع، التحليلات المالية المتقدمة، والتكامل البنكي، مع روبوتات ذكية تعمل تلقائياً.

## المعمارية التقنية

### قاعدة البيانات: `ntbass` (MongoDB)
- المجموعات الرئيسية: accounts, products, sales, customers, expenses, purchases, cash_boxes
- المجموعات الجديدة (الروبوتات): auto_reports, report_pdfs, collection_reports, reorder_recommendations, stockout_predictions, debt_reminders, sms_log, push_notifications

### Backend (FastAPI)
```
/app/backend/
├── server.py           # الخادم الرئيسي (~11,800 سطر)
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
├── routes/                     # المسارات المقسمة
├── models/                     # النماذج
├── utils/                      # أدوات مساعدة
├── tests/                      # اختبارات
├── docs/                       # توثيق
└── config/database.py
```

### Frontend (React + Tailwind + Shadcn)
```
/app/frontend/src/pages/
├── RobotsPage.js          # جديد - لوحة تحكم الروبوتات
├── admin/SaasAdminPage.js # محدث - زر الانتقال للروبوتات
├── SmartDashboardPage.js
├── AIChatPage.js
├── BankingPage.js
└── ...
```

## الميزات المنجزة

### الروبوتات الذكية (مارس 2026)
- [x] روبوت المخزون - مراقبة، توصيات إعادة طلب، توقع نفاد (scikit-learn)
- [x] روبوت الديون - متابعة، تذكيرات SMS، تحليل أداء التحصيل
- [x] روبوت التقارير - يومي/أسبوعي/شهري + PDF (reportlab) + بريد إلكتروني
- [x] مدير الروبوتات المركزي (RobotManager) - startup/shutdown
- [x] API endpoints: status, run, restart, stop-all, start-all
- [x] خدمات: NotificationService, SMSService(MOCKED), EmailService
- [x] لوحة تحكم مباشرة (Frontend Dashboard) مع:
  - عرض حالة النظام والروبوتات النشطة
  - بطاقات لكل روبوت مع إحصائيات حية
  - أزرار تشغيل/إعادة تشغيل/إيقاف
  - تحديث تلقائي كل 10 ثواني
  - وصول من صفحة SaaS Admin

### البنية التحتية
- [x] نظام SaaS متعدد المستأجرين
- [x] JWT + CORS + Rate Limiting
- [x] PWA (manifest + service worker)

### الذكاء الاصطناعي
- [x] محادثة AI مع GPT-4o
- [x] 8 وكلاء ذكاء اصطناعي

## بيانات الاختبار
- **مدير عام**: admin@ntcommerce.com / Admin@2024
- **مستأجر**: ncr@ntcommerce.com / Test@123

## نتائج الاختبارات
- Backend: 17/17 (100%)
- Frontend: 12/12 (100%)
- Test reports: /app/test_reports/iteration_60.json, iteration_61.json

## المهام المتبقية (Backlog)

### P1
- [ ] تقسيم server.py (~11,800 سطر) إلى modules أصغر
- [ ] اختبارات وحدة شاملة (تغطية >80%)

### P2
- [ ] ربط SMS مع مزود حقيقي (Twilio)
- [ ] ربط WhatsApp مع Meta API
- [ ] إشعارات push عبر Service Worker
- [ ] حماية متقدمة (2FA, brute-force)

### P3
- [ ] روبوتات إضافية (العملاء، التسعير، الصيانة)
- [ ] استيراد بيانات Access
- [ ] تكامل بنكي حقيقي

---
*آخر تحديث: 13 مارس 2026*
*الإصدار: 5.1 - Intelligent Robots + Dashboard*
