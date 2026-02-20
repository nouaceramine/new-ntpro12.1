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
- **فتح/غلق الحصة من POS مباشرة**
- شريط معلومات الجلسة يعرض:
  - كود الحصة
  - إحصائيات: نقدي، دين، إجمالي، عدد العمليات
- زر "فتح حصة" عند عدم وجود حصة مفتوحة
- زر "غلق الحصة" مع نافذة تأكيد
- زر "التفاصيل" لعرض تفاصيل الحصة الكاملة

#### Backup System for Tenants ✅
- نظام نسخ احتياطي متاح لكل مستأجر في صفحة الإعدادات
- **الوظائف**:
  - تصدير JSON/CSV
  - استيراد من JSON
  - إعدادات النسخ التلقائي (يومي/أسبوعي/شهري)
  - تحديد عدد النسخ المحفوظة
  - زر "نسخ الآن"

#### French Language Support ✅
- دعم كامل للغة الفرنسية
- صفحة إضافة منتج مترجمة بالكامل
- لوحة التحكم مترجمة
- جميع النماذج والأزرار مترجمة

---

## API Endpoints Summary

### Daily Sessions APIs
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/daily-sessions/current` | GET | Tenant | Get current open session |
| `/api/daily-sessions` | POST | Tenant | Open new session |
| `/api/daily-sessions/{id}/close` | PUT | Tenant | Close session |
| `/api/daily-sessions/generate-code` | GET | Tenant | Generate session code |

### Cash Boxes APIs
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/cash-boxes` | GET | Tenant | Get all cash boxes |
| `/api/cash/deposit` | POST | Tenant | Deposit to cash box |
| `/api/cash/withdraw` | POST | Tenant | Withdraw from cash box |

### Stats APIs
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/stats` | GET | Tenant | Get dashboard stats including total_cash |
| `/api/dashboard/sales-stats` | GET | Tenant | Get sales statistics |

### Backup APIs
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/backup/auto-settings` | GET | Tenant | Get auto-backup settings |
| `/api/backup/auto-settings` | POST | Tenant | Save auto-backup settings |
| `/api/backup/run-auto` | POST | Tenant | Run manual backup |

---

## Database Schema

### cash_boxes collection
```javascript
{
  id: String,      // "cash", "bank", "wallet", "safe"
  name: String,    // Arabic name
  name_fr: String, // French name
  type: String,    // cash, bank, wallet
  balance: Number,
  updated_at: String (optional)
}
```

### daily_sessions collection
```javascript
{
  id: String,
  code: String,
  user_id: String,
  user_name: String,
  opening_cash: Number,
  closing_cash: Number (nullable),
  opened_at: String,
  closed_at: String (nullable),
  total_sales: Number,
  cash_sales: Number,
  credit_sales: Number,
  sales_count: Number,
  status: String, // "open" or "closed"
  notes: String
}
```

---

## Known Fixes

### Feb 20, 2026
- **Fixed CashBoxResponse schema**: Made `updated_at` field optional in `/app/backend/models/schemas.py` to prevent Pydantic validation errors

---

## Test Reports
- `/app/test_reports/iteration_52.json` - POS barcode support tests
- `/app/test_reports/iteration_53.json` - Session management, French translations, Backup system tests

---

## Upcoming Tasks (P1)

- [ ] إكمال تقسيم `server.py` إلى ملفات routes منفصلة:
  - `/routes/products.py`
  - `/routes/sales.py`
  - `/routes/customers.py`
  - `/routes/employees.py`
- [ ] تنفيذ تعيين اختصارات المنتجات في POS
- [ ] ربط قسم تنبيهات الأخطاء بـ API حقيقي

## Future Tasks (P2)

- [ ] تحسين أداء صفحة المنتجات (virtualization)
- [ ] توسيع اختبارات E2E
- [ ] تحسينات على نظام الإشعارات

---

*Last Updated: February 20, 2026*
