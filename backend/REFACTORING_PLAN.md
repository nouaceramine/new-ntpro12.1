# خطة إعادة هيكلة server.py
# Server.py Refactoring Plan

## الملف الحالي: /app/backend/server.py
- **الحجم**: 12,883 سطر
- **عدد الـ endpoints**: 378+
- **الحالة**: يعمل بشكل كامل

## الهيكلة المستهدفة

```
/app/backend/
├── server.py                 # Main app, middleware, startup (500 lines max)
├── config/
│   └── database.py           # ✅ موجود ويعمل
├── models/
│   └── schemas.py            # ✅ موجود ويعمل  
├── utils/
│   ├── auth.py               # ✅ موجود ويعمل
│   └── dependencies.py       # ✅ موجود ويعمل
├── routes/
│   ├── auth.py               # 🟡 موجود (غير مستخدم)
│   ├── saas.py               # 🟡 موجود (غير مستخدم)
│   ├── saas_admin.py         # 🟡 جديد - نموذج للهيكلة
│   ├── products.py           # 🔴 يحتاج إنشاء (18 endpoints)
│   ├── sales.py              # 🔴 يحتاج إنشاء (14 endpoints)
│   ├── customers.py          # 🔴 يحتاج إنشاء (9 endpoints)
│   ├── employees.py          # 🔴 يحتاج إنشاء (15 endpoints)
│   ├── inventory.py          # 🔴 يحتاج إنشاء
│   ├── reports.py            # 🔴 يحتاج إنشاء
│   ├── notifications.py      # 🔴 يحتاج إنشاء (22 endpoints)
│   └── ...
└── services/                 # Business logic (optional)
```

## توزيع الـ Endpoints حسب القسم

| القسم | عدد الـ Endpoints | الأولوية |
|-------|-------------------|----------|
| saas | 39 | P0 |
| notifications | 22 | P1 |
| products | 18 | P1 |
| employees | 15 | P1 |
| sales | 14 | P2 |
| customers | 9 | P2 |
| suppliers | 8 | P2 |
| ... | ... | P3 |

## خطوات التنفيذ (تدريجي)

### المرحلة 1: التحضير ✅
- [x] إنشاء البنية الأساسية (config, models, utils)
- [x] إنشاء ملف نموذجي (routes/saas_admin.py)
- [x] التوثيق

### المرحلة 2: نقل SaaS (39 endpoint)
- [ ] إكمال routes/saas_admin.py بجميع الـ endpoints
- [ ] إضافة الـ router في server.py
- [ ] حذف الكود القديم
- [ ] اختبار شامل

### المرحلة 3: نقل Products (18 endpoint)
- [ ] إنشاء routes/products.py
- [ ] نقل الـ endpoints
- [ ] اختبار

### المرحلة 4-N: باقي الأقسام
...

## ملاحظات مهمة

1. **لا تحذف الكود القديم قبل اختبار الجديد**
2. **اختبر بعد كل قسم**
3. **احتفظ بنسخة احتياطية**: `/app/backend/server.py.backup`
4. **الـ endpoints المشتركة**: بعض الـ functions تستخدم في عدة أماكن

## الملفات المرجعية

- `/app/backend/routes/saas_admin.py` - نموذج للهيكلة الجديدة
- `/app/backend/server.py.backup` - نسخة احتياطية

---
تاريخ الإنشاء: 14 فبراير 2026
