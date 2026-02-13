# NT Commerce - Product Requirements Document

## Project Overview
NT Commerce هو نظام SaaS متكامل لإدارة المبيعات والمخزون، يدعم اللغة العربية والفرنسية، مع واجهة مستخدم احترافية وميزات متقدمة.

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

#### 1. إعادة تصميم صفحة POS ✅
- تصميم جديد بثلاثة أعمدة:
  - الشريط الأيسر: قائمة المهام مع اختصارات لوحة المفاتيح (Ctrl+0-9)
  - المنطقة الوسطى: جدول المنتجات المضافة للبيع
  - الشريط الأيمن: 20 زر اختصار للمنتجات
- عرض كود البيع والإجمالي في الأعلى
- تحذير لفتح حصة جديدة قبل البيع
- أزرار (بيع، عرض سعر، تأكيد، إلغاء)

#### 2. تعديل/حذف المشتريات ✅
- أزرار جديدة في جدول المشتريات (عرض، تعديل، حذف)
- Backend APIs:
  - `PUT /api/purchases/{id}` - تعديل المبلغ المدفوع والملاحظات
  - `DELETE /api/purchases/{id}` - حذف المشتريات مع عكس تغييرات المخزون
  - `GET /api/purchases/{id}` - عرض تفاصيل المشتريات

#### 3. نظام Feature Flags ✅
- صفحة إدارة الميزات لـ Super Admin (`/saas-admin/feature-flags`)
- تحكم في الميزات لكل خطة اشتراك
- فئات الميزات: المبيعات، المخزون، المشتريات، الزبائن، التقارير، التوصيل، الإصلاحات، المتجر الإلكتروني

#### 4. إعدادات الصوت ✅
- تبويب جديد "الصوت" في صفحة الإعدادات
- تفعيل/تعطيل الأصوات:
  - صوت البيع الناجح
  - صوت الخطأ
  - صوت الإشعارات
  - صوت المسح (الباركود)
- شريط التحكم بمستوى الصوت
- زر اختبار الصوت

#### 5. صفحة الأسعار الترويجية ✅
- صفحة عامة (`/pricing`) بدون تسجيل دخول
- عرض جميع خطط الاشتراك
- خيارات شهري/سنوي مع خصم 20%
- دعم اللغة العربية والفرنسية
- تصميم احترافي ومتجاوب

#### 6. نظام المتجر الإلكتروني ✅
- صفحة إدارة المتجر (`/store`)
- ميزات:
  - تفعيل/تعطيل المتجر
  - إعدادات المتجر (الاسم، الرابط، الوصف)
  - التصميم (الشعار، اللون الرئيسي)
  - معلومات التواصل
  - التوصيل والدفع (COD - الدفع عند الاستلام)
  - إدارة المنتجات المعروضة
  - إدارة الطلبات وحالاتها
- Backend APIs:
  - `GET/PUT /api/store/settings`
  - `GET/POST/DELETE /api/store/products`
  - `GET /api/store/orders`
  - `PUT /api/store/orders/{id}/status`
  - `GET /api/shop/{slug}` (عام)
  - `POST /api/shop/{slug}/order` (عام)

## Database Schema

### New Collections
```javascript
// store_settings
{
  enabled: Boolean,
  store_name: String,
  store_slug: String,
  description: String,
  logo_url: String,
  primary_color: String,
  contact_phone: String,
  cod_enabled: Boolean,
  delivery_enabled: Boolean,
  delivery_fee: Number
}

// store_products
{
  id: String,
  product_id: String,
  is_active: Boolean,
  created_at: DateTime
}

// store_orders
{
  id: String,
  order_number: String,
  customer_name: String,
  customer_phone: String,
  delivery_address: String,
  items: Array,
  total: Number,
  status: String, // pending, confirmed, processing, shipped, delivered, cancelled
  payment_method: String // cod
}
```

## Test Credentials
- **Super Admin**: `super@ntcommerce.com`
- **Test Tenant**: `test@test.com` / `test123`

## API Endpoints Summary

### Store APIs
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/store/settings` | GET | Admin | Get store settings |
| `/api/store/settings` | PUT | Admin | Update store settings |
| `/api/store/products` | GET | Admin | Get store products |
| `/api/store/products` | POST | Admin | Add product to store |
| `/api/store/products/{id}` | DELETE | Admin | Remove from store |
| `/api/store/orders` | GET | Admin | Get all orders |
| `/api/store/orders/{id}/status` | PUT | Admin | Update order status |
| `/api/shop/{slug}` | GET | Public | Get public store |
| `/api/shop/{slug}/order` | POST | Public | Create order (COD) |

### Public APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/saas/plans/public` | GET | Get pricing plans |

## Upcoming Tasks (P2)

### Backend Refactoring
- تقسيم `server.py` إلى ملفات منفصلة (routes, models, services)

### Frontend Refactoring
- تقسيم `SaasAdminPage.js` إلى مكونات أصغر

### E2E Testing
- إضافة اختبارات شاملة للمسارات الحرجة

### Public Store UI
- إنشاء صفحة المتجر العامة للزبائن (`/shop/{slug}`)
- صفحة عربة التسوق
- صفحة تأكيد الطلب

---
*Last Updated: February 2026*
