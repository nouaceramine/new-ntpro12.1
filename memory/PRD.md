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

#### 1. إعادة تصميم صفحة POS ✅ (UPDATED - Feb 14, 2026)
- **تغيير رئيسي**: إدماج صفحة POS داخل Layout الرئيسي للتطبيق
- تصميم جديد بثلاثة أعمدة مع Grid Layout (صفحة واحدة بدون scroll):
  - الشريط الأيسر (col-span-2): خانة بحث + زر إضافة منتج + قائمة المهام
  - المنطقة الوسطى (col-span-8): جدول المنتجات المضافة للبيع
  - الشريط الأيمن (col-span-2): 10 زر اختصار للمنتجات (مصغّر)
- العنوان يظهر "نقطة البيع - NT Commerce"
- **إصلاح تخطيط RTL** ✅ (Feb 14, 2026):
  - تم إصلاح ترتيب الأعمدة في واجهة RTL
  - "مهام البيع" الآن على اليسار (صحيح)
  - "اختصارات" الآن على اليمين (صحيح)
- **مهام البيع تعمل الآن:**
  - قائمة المنتجات (Ctrl+0) → فتح نافذة اختيار المنتجات
  - بالعائلة (Ctrl+1) → فتح نافذة المنتجات مع فلتر العائلة
  - الزبائن (Ctrl+2) → فتح نافذة اختيار الزبائن
  - عائلات الزبائن (Ctrl+3) → فتح نافذة الزبائن
  - ملاحظة (Ctrl+4) → فتح نافذة إضافة ملاحظة للفاتورة
  - إرجاع (Ctrl+5) → تفعيل/تعطيل وضع الإرجاع (badge أحمر)
  - إيداع (Ctrl+6) → فتح نافذة إيداع في الصندوق
  - سحب (Ctrl+7) → فتح نافذة سحب من الصندوق
  - تقارير (Ctrl+8) → الانتقال لصفحة التقارير
  - السجل (Ctrl+9) → فتح نافذة سجل المبيعات
- **دعم الطباعة الحرارية المحسّن** ✅ (Feb 14, 2026):
  - دعم طابعات 58mm و 80mm
  - ESC/POS متوافق مع جميع موديلات الطابعات الحرارية
  - دعم RTL/LTR في الإيصالات
  - عرض المدفوع والباقي
  - عرض رسوم التوصيل
  - اسم البائع في الإيصال
- وضع الإرجاع مع badge متحرك في الـ header
- **10 أيقونات اختصار** معروضة بشكل صحيح

#### 2. تعديل/حذف المشتريات ✅
- أزرار جديدة في جدول المشتريات (عرض، تعديل، حذف)
- Backend APIs:
  - `PUT /api/purchases/{id}` - تعديل المبلغ المدفوع والملاحظات
  - `DELETE /api/purchases/{id}` - حذف المشتريات مع عكس تغييرات المخزون
  - `GET /api/purchases/{id}` - عرض تفاصيل المشتريات

#### 3. نظام Feature Flags ✅ (UPDATED - Feb 13, 2026)
- صفحة إدارة الميزات لـ Super Admin (`/saas-admin/feature-flags`)
- تحكم في الميزات لكل خطة اشتراك
- فئات الميزات: المبيعات، المخزون، المشتريات، الزبائن، التقارير، التوصيل، الإصلاحات، المتجر الإلكتروني
- **تم تنفيذ منطق Feature Flags في Frontend:**
  - إضافة `features` و `limits` في `AuthContext.js`
  - دالة `isFeatureEnabled(categoryKey, subFeatureKey)` للتحقق من تفعيل الميزات
  - تصفية عناصر القائمة الجانبية بناءً على الميزات المفعلة في `Layout.js`
  - كل قسم في القائمة الجانبية مرتبط بـ `featureKey`

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

#### 6. نظام المتجر الإلكتروني ✅ (COMPLETED - Feb 13, 2026)
- صفحة إدارة المتجر (`/store`)
- **صفحة المتجر العام (`/shop/{slug}`)** - تم تنفيذها بالكامل:
  - عرض المنتجات المتاحة
  - سلة التسوق
  - نموذج الطلب مع معلومات التوصيل
  - الدفع عند الاستلام (COD)
  - دعم عربي/فرنسي
- ميزات إدارة المتجر:
  - تفعيل/تعطيل المتجر
  - إعدادات المتجر (الاسم، الرابط، الوصف)
  - التصميم (الشعار، اللون الرئيسي)
  - معلومات التواصل
  - التوصيل والدفع
  - إدارة المنتجات المعروضة
  - إدارة الطلبات وحالاتها
- **تحسينات Backend:**
  - تخزين `store_slug` في `main_db.store_slugs` للوصول العام
  - البحث عن المستأجر باستخدام slug من القاعدة الرئيسية
  - تحديث المخزون تلقائياً عند إنشاء طلب

## Database Schema

### New Collections
```javascript
// main_db.store_slugs (NEW - for public store access)
{
  tenant_id: String,
  store_slug: String (unique),
  enabled: Boolean,
  store_name: String,
  updated_at: DateTime
}

// store_settings (tenant db)
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
  delivery_fee: Number,
  free_delivery_threshold: Number,
  min_order_amount: Number
}

// store_products (tenant db)
{
  id: String,
  product_id: String,
  is_active: Boolean,
  is_featured: Boolean,
  store_price: Number,
  created_at: DateTime
}

// store_orders (tenant db)
{
  id: String,
  order_number: String,
  store_slug: String,
  customer_name: String,
  customer_phone: String,
  customer_email: String,
  delivery_address: String,
  delivery_city: String,
  delivery_wilaya: String,
  items: Array,
  subtotal: Number,
  delivery_fee: Number,
  total: Number,
  notes: String,
  payment_method: String, // cod
  status: String, // pending, confirmed, processing, shipped, delivered, cancelled
  payment_status: String, // unpaid, paid
  created_at: DateTime
}
```

## Test Credentials
- **Super Admin**: `super@ntcommerce.com` / `admin123`
- **Test Tenant**: `demo@demo.com` / `demo123`
- **Test Store Slug**: `demo-store`

## API Endpoints Summary

### Feature Flags APIs
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/unified-login` | POST | Public | Login with features & limits returned |
| `/api/auth/me` | GET | Auth | Get user with features & limits |
| `/api/saas/plans/{id}/features` | PUT | SuperAdmin | Update plan features |

### Store APIs
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/store/settings` | GET | Admin | Get store settings |
| `/api/store/settings` | PUT | Admin | Update store settings (saves slug to main_db) |
| `/api/store/products` | GET | Admin | Get store products |
| `/api/store/products` | POST | Admin | Add product to store |
| `/api/store/products/{id}` | DELETE | Admin | Remove from store |
| `/api/store/orders` | GET | Admin | Get all orders |
| `/api/store/orders/{id}/status` | PUT | Admin | Update order status |
| `/api/shop/{slug}` | GET | **Public** | Get public store (uses main_db lookup) |
| `/api/shop/{slug}/order` | POST | **Public** | Create order (COD, updates stock) |

### Public APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/saas/plans/public` | GET | Get pricing plans |
| `/api/delivery/wilayas` | GET | Get delivery wilayas |
| `/api/sales/generate-code` | GET | Generate new sale code |

## Performance Optimizations (Feb 13, 2026)

### Products Page Performance
- ✅ Backend Pagination: `/api/products/paginated` endpoint
- ✅ Lazy Loading Images: `LazyImage` component
- ✅ Configurable items per page (stored in localStorage)
- ✅ Installed `@tanstack/react-virtual` for future virtualization

### POS Page Performance
- ✅ Single page design (no scrolling)
- ✅ Reduced shortcuts from 20 to 10
- ✅ Efficient re-renders with useCallback

### Thermal Printing Support
- ✅ ESC/POS compatible HTML receipt generation
- ✅ Supports all thermal printer models (80mm width)
- ✅ Auto-print option in receipt settings
- ✅ RTL/LTR language support in receipts

## Upcoming Tasks (P1)

### Backend Refactoring
- تقسيم `server.py` إلى ملفات منفصلة (routes, models, services)
- الملف حالياً 12,332 سطر ويحتاج تقسيم

### Frontend Refactoring
- تقسيم `SaasAdminPage.js` إلى مكونات أصغر

### E2E Testing
- إضافة اختبارات شاملة للمسارات الحرجة

## Test Files
- `/app/backend/tests/test_pos_redesign.py` - اختبارات POS redesign (6 tests - all passing)
- `/app/test_reports/iteration_50.json` - Frontend tests for POS task menu (12 tests - all passing)

---
*Last Updated: February 13, 2026*
