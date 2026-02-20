# NT Commerce - Product Requirements Document

## Project Overview
NT Commerce هو نظام SaaS متكامل لإدارة المبيعات والمخزون، يدعم اللغة العربية والفرنسية، مع واجهة مستخدم احترافية وميزات متقدمة.

## Test Credentials
- **Super Admin**: `admin@ntcommerce.com` / `Admin@2024`
- **Tenant**: `ncr@ntcommerce.com` / `Test@123`

---

## Core Features Implemented

### Phase 1: Core Sales & Inventory (COMPLETED)
- ✅ نقطة البيع (POS)
- ✅ إدارة المنتجات والمخزون
- ✅ إدارة الزبائن والديون
- ✅ إدارة الموردين والمشتريات
- ✅ التقارير والتحليلات
- ✅ نظام الحصص اليومية

### Phase 2: SaaS & Integrations (COMPLETED)
- ✅ SendGrid للإشعارات البريدية
- ✅ Stripe لنظام الدفع والاشتراكات
- ✅ نظام متعدد المستأجرين (Multi-tenant)

### Phase 3: Latest Updates (COMPLETED - Feb 2026)

#### POS Page Features ✅
- تصميم ثلاثة أعمدة مع Grid Layout
- 18 زر اختصار للمنتجات
- دعم قارئ الباركود
- مهام البيع (10 عناصر مع اختصارات لوحة المفاتيح)
- دعم الطباعة الحرارية (58mm و 80mm)

#### POS Session Management ✅ (Feb 20, 2026)
- فتح/غلق الحصة من POS مباشرة
- شريط معلومات الجلسة يعرض: كود الحصة، نقدي، دين، إجمالي، عدد العمليات
- زر "غلق الحصة" مع نافذة تأكيد
- زر "التفاصيل" لعرض تفاصيل الحصة الكاملة

#### POS Product Shortcuts ✅ (Feb 20, 2026)
- **18 صندوق اختصار** مع دعم تعيين المنتجات
- **النقر بالزر الأيمن** يفتح نافذة تعديل الاختصار
- **اختيار المنتج** من قائمة منسدلة
- **اختيار اللون** من شبكة 20 لون
- **حفظ في localStorage** للاحتفاظ بالإعدادات
- **عرض اسم المنتج والسعر** في الصندوق

#### System Errors API ✅ (Feb 20, 2026)
- **API جديد** لإدارة أخطاء النظام (/api/saas/system-errors)
- **Endpoints**:
  - GET / - جلب قائمة الأخطاء مع الإحصائيات
  - POST / - إنشاء خطأ جديد
  - POST /{id}/fix - تنفيذ الإصلاح التلقائي
  - POST /{id}/resolve - تحديد الخطأ كمحلول
  - DELETE /resolved - حذف جميع الأخطاء المحلولة
  - DELETE /{id} - حذف خطأ معين
  - POST /maintenance/{action} - تنفيذ إجراءات الصيانة

#### System Alerts Frontend ✅ (Feb 20, 2026)
- **بيانات حقيقية** من API (لم يعد يستخدم mock data)
- **بطاقات الإحصائيات**: إجمالي، حرجة، تحذيرات، معلومات، محلولة، اليوم
- **قائمة الأخطاء** مع:
  - أيقونات النوع واللون حسب الأهمية
  - اسم المستأجر والوقت النسبي
  - أزرار الإصلاح التلقائي والحل اليدوي
- **إجراءات الصيانة السريعة**:
  - مسح الكاش
  - إعادة اتصال قاعدة البيانات
  - إعادة تشغيل الخدمات
  - فحص النظام

#### Backup System for Tenants ✅
- نظام نسخ احتياطي متاح لكل مستأجر في صفحة الإعدادات
- تصدير JSON/CSV، استيراد، نسخ تلقائي

#### French Language Support ✅
- دعم كامل للغة الفرنسية
- صفحة إضافة منتج مترجمة بالكامل

---

## API Endpoints Summary

### System Errors APIs (NEW)
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/saas/system-errors` | GET | Super Admin | Get all errors with stats |
| `/api/saas/system-errors` | POST | None | Create new error |
| `/api/saas/system-errors/{id}/fix` | POST | Super Admin | Auto-fix error |
| `/api/saas/system-errors/{id}/resolve` | POST | Super Admin | Mark as resolved |
| `/api/saas/system-errors/resolved` | DELETE | Super Admin | Clear resolved errors |
| `/api/saas/system-errors/{id}` | DELETE | Super Admin | Delete specific error |
| `/api/saas/system-errors/maintenance/{action}` | POST | Super Admin | Run maintenance |

### Daily Sessions APIs
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/daily-sessions/current` | GET | Tenant | Get current open session |
| `/api/daily-sessions` | POST | Tenant | Open new session |
| `/api/daily-sessions/{id}/close` | PUT | Tenant | Close session |

### Stats APIs
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/stats` | GET | Tenant | Get dashboard stats including total_cash |

---

## Database Schema

### system_errors collection (NEW)
```javascript
{
  id: String,           // UUID
  type: String,         // api, database, payment, auth, system, integration
  severity: String,     // critical, warning, info
  message: String,
  tenant_id: String,
  tenant_name: String,
  timestamp: String,    // ISO format
  status: String,       // active, resolved
  auto_fixable: Boolean,
  fix_action: String,   // reconnect_db, clear_cache, clear_sessions, etc.
  details: Object,
  resolved_at: String,
  resolved_by: String
}
```

---

## Code Architecture

### Backend Routes Structure
```
/app/backend/
├── server.py           # Main server (11,416 lines)
├── routes/
│   ├── saas_routes.py       # SaaS management
│   ├── database_routes.py   # DB import/export
│   └── system_errors.py     # NEW: System errors API
└── models/
    └── schemas.py           # Pydantic models
```

### Frontend Components
```
/app/frontend/src/
├── pages/
│   ├── POSPage.js                    # POS with shortcuts
│   ├── admin/
│   │   └── components/
│   │       └── SystemAlertsSection.js # Real API connection
│   └── SettingsPage.js               # Backup system
└── components/
    └── BackupSystem.js               # Tenant backup
```

---

## Test Reports
- `/app/test_reports/iteration_53.json` - POS session management, French translations
- `/app/test_reports/iteration_54.json` - System Errors API, POS Shortcuts (100% pass)

---

## Completed Tasks (Feb 20, 2026)

### ✅ P1: اختصارات المنتجات في POS
- 18 صندوق اختصار مع تعيين المنتجات
- نافذة تعديل بالنقر بالزر الأيمن
- اختيار الألوان والمنتجات
- حفظ في localStorage

### ✅ P2: ربط تنبيهات الأخطاء بـ API حقيقي
- إنشاء `/app/backend/routes/system_errors.py`
- 7 endpoints للـ CRUD والصيانة
- تحديث Frontend لاستخدام API حقيقي
- إزالة جميع البيانات الوهمية (Mock)

### ⏳ P1: تقسيم server.py (جزئي)
- ✅ أضفنا `system_errors.py` route جديد
- ⏳ يتبقى نقل: products, sales, customers, employees routes

---

## Upcoming Tasks (P1)

- [ ] إكمال تقسيم `server.py`:
  - `/routes/products.py` (~18 endpoint)
  - `/routes/sales.py` (~14 endpoint)
  - `/routes/customers.py` (~9 endpoint)
  - `/routes/employees.py`

## Future Tasks (P2)

- [ ] تحسين أداء صفحة المنتجات (virtualization)
- [ ] توسيع اختبارات E2E
- [ ] تصدير تقارير PDF

---

## 3rd Party Integrations
- **OpenAI GPT-4o**: Uses Emergent LLM Key
- **SendGrid**: Email notifications
- **Stripe**: Payments and subscriptions
- **mdbtools**: Microsoft Access file import

---

*Last Updated: February 20, 2026*
