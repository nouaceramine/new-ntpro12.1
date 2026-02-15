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

#### 1. نظام تتبع المنتجات المعطلة ✅ (NEW - Feb 14, 2026)
- **تبويب جديد في صفحة المنتجات** للمنتجات المعطلة
- **تسجيل المنتجات المعطلة** مع:
  - اختيار المنتج والكمية
  - تحديد سبب العطل (عيب تصنيع، تلف شحن، تلف تخزين، منتهي الصلاحية، أخرى)
  - تحديد الإجراء (قيد الانتظار، إرجاع للمورد، إتلاف، إصلاح، بيع بتخفيض)
  - إضافة ملاحظات
- **الخصم التلقائي من المخزون** عند تسجيل منتج معطل
- **إنشاء طلب إرجاع تلقائي** للمورد عند اختيار "إرجاع للمورد"
- **إشعارات تلقائية** عند تجاوز نسبة المعطلات 5%
- **إحصائيات شاملة**:
  - إجمالي المعطلات، معلق، قيد التنفيذ، مكتمل
  - إجمالي تكلفة الخسائر
  - تقارير حسب السبب والمورد
- **فلاتر متقدمة** (حسب الحالة والسبب)
- **API Endpoints**:
  - `POST /api/defective-products` - تسجيل منتج معطل
  - `GET /api/defective-products` - قائمة المعطلات
  - `GET /api/defective-products/stats` - إحصائيات
  - `PUT /api/defective-products/{id}` - تحديث الحالة
  - `DELETE /api/defective-products/{id}` - حذف (مع خيار استعادة المخزون)
  - `GET /api/supplier-returns` - طلبات الإرجاع للموردين
  - `PUT /api/supplier-returns/{id}` - تحديث حالة الإرجاع

#### 2. إعادة تصميم صفحة POS ✅ (UPDATED - Feb 14, 2026)
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
- **دعم قارئ الباركود** ✅ (Feb 14, 2026):
  - الكشف التلقائي عن إدخال الباركود السريع (<50ms بين الأحرف)
  - البحث التلقائي عند الضغط على Enter
  - إضافة المنتج تلقائياً للسلة عند مطابقة الباركود
  - مؤشر بصري أخضر أثناء مسح الباركود
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
- ✅ Supports all thermal printer models (58mm & 80mm width)
- ✅ **إعدادات حجم الطابعة** في صفحة الإعدادات (تبويب الطابعة)
- ✅ Auto-print option in receipt settings
- ✅ RTL/LTR language support in receipts

## Phase 4: Latest Updates (Feb 14, 2026)

### قسم تنبيهات الأخطاء في SaaS Admin ✅
- تبويب جديد "الأخطاء" في لوحة تحكم SaaS Admin
- إحصائيات الأخطاء (إجمالي، حرجة، تحذيرات، معلومات، محلولة، اليوم)
- قائمة الأخطاء مع تفاصيل كاملة (النوع، الشدة، المستأجر، الوقت)
- **إصلاح تلقائي** للأخطاء القابلة للإصلاح
- **إصلاح يدوي** للأخطاء الأخرى
- فلتر الأخطاء (الكل، نشطة، محلولة، حرجة، تحذيرات)
- تصدير سجل الأخطاء
- إجراءات صيانة سريعة (مسح الكاش، إعادة اتصال DB، إعادة تشغيل، فحص النظام)
- **ملاحظة: يستخدم بيانات وهمية (MOCK) للعرض التجريبي**

### توافق الهاتف (Responsive Design) ✅
- صفحة POS متوافقة مع الهاتف:
  - أزرار سريعة (منتج، إرجاع، زبون، سجل) بدلاً من القائمة الجانبية
  - عرض المنتجات كبطاقات بدلاً من الجدول
  - أزرار التأكيد والإلغاء بعرض كامل
- لوحة التحكم متوافقة مع الهاتف
- القائمة الجانبية تعمل على الهاتف (hamburger menu)
- SaaS Admin متوافق مع الهاتف

### إعادة هيكلة Frontend ✅ (Feb 14, 2026)
تم تقسيم `SaasAdminPage.js` من 2170 سطر إلى ملفات منفصلة:
- `/components/SystemAlertsSection.js` - قسم تنبيهات الأخطاء (391 سطر)
- `/components/MonitoringSection.js` - قسم المراقبة (190 سطر)
- `/components/FinanceReportsSection.js` - قسم التقارير المالية (361 سطر)
- `SaasAdminPage.js` الرئيسي (1294 سطر)

### إعادة هيكلة Backend (تم جزء كبير - Feb 14, 2026)
- تم إنشاء `/config/database.py` - إعدادات قاعدة البيانات
- تم تحديث `/utils/auth.py` - دوال المصادقة
- **تم إنشاء `/routes/saas_routes.py`** - جميع routes الـ SaaS Admin (39 endpoint، 1117 سطر)
- **تم تقليل `server.py`** من 12,883 سطر إلى 11,393 سطر (حذف ~1490 سطر)
- الملف لا يزال يحتاج لمزيد من التقسيم للأقسام الأخرى

### اختبارات E2E ✅
- تم إنشاء `/tests/test_e2e.py` مع اختبارات شاملة:
  - اختبارات المصادقة (تسجيل الدخول للمستأجر والمدير)
  - اختبارات المنتجات (استعلام، إنشاء، بحث)
  - اختبارات الزبائن
  - اختبارات المبيعات/POS
  - اختبارات التقارير
  - اختبارات SaaS Admin
  - اختبارات الإعدادات

## Upcoming Tasks (P1)

- إكمال تقسيم `server.py` إلى ملفات routes منفصلة:
  - `/routes/products.py` - المنتجات (18 endpoint)
  - `/routes/sales.py` - المبيعات (14 endpoint)
  - `/routes/customers.py` - الزبائن (9 endpoint)
  - `/routes/employees.py` - الموظفين (15 endpoint)
- ربط قسم تنبيهات الأخطاء بـ API حقيقي

### Backend Refactoring (In Progress)
- ✅ تم نقل SaaS routes إلى `/routes/saas_routes.py`
- باقي الأقسام للنقل: products, sales, customers, employees, notifications

### Frontend Refactoring
- تقسيم `SaasAdminPage.js` إلى مكونات أصغر

### E2E Testing
- إضافة اختبارات شاملة للمسارات الحرجة

## Recent Fixes (Feb 14, 2026 - Session 3)

### 1. تفعيل 18 اختصار في صفحة POS ✅
- **التغيير**: زيادة عدد الاختصارات من 10 إلى 18
- **التنسيق**: 6 صفوف × 3 أعمدة
- **الملف**: `/app/frontend/src/pages/POSPage.js`

### 2. إعادة هيكلة server.py (المرحلة الأولى) ✅
- **تم نقل**: جميع SaaS endpoints (39 endpoint) إلى `/routes/saas_routes.py`
- **الحجم الجديد**: 11,393 سطر (من 12,883)
- **تم حذف**: ~1,490 سطر من server.py
- **الأقسام المنقولة**:
  - Plans routes
  - Tenants routes
  - Agents routes
  - Registration routes
  - Database management routes
  - Stats & Monitoring routes

### 3. إصلاح خطأ frontend في SaasAdminPage ✅
- **المشكلة**: `Cannot read properties of undefined (reading 'toLocaleString')`
- **السبب**: عدم تطابق أسماء الحقول (price_monthly vs monthly_price)
- **الحل**: إضافة fallback values للحقول المالية

### 4. إعادة تهيئة النظام للإنتاج ✅
- **حذف جميع البيانات التجريبية**: 15 قاعدة بيانات tenant
- **تنظيف قواعد البيانات القديمة**: ntcommerce, nt_pos_db, test_database
- **إنشاء خطط اشتراك جديدة**:
  - المبتدئ: 2,900 دج/شهر
  - الاحترافي: 5,900 دج/شهر (الأكثر طلباً)
  - المؤسسات: 9,900 دج/شهر
- **تحديث حساب المدير الأعلى**:
  - البريد: admin@ntcommerce.com
  - كلمة المرور: Admin@2024
- **السكريبتات المنشأة**:
  - `/app/backend/scripts/reset_system.py` - لإعادة تهيئة النظام
  - `/app/backend/scripts/init_production.py` - لتهيئة الإنتاج

## Recent Updates (Feb 15, 2026)

### ميزة استيراد/تصدير قاعدة البيانات الخارجية ✅ (NEW)

#### الوظائف المنفذة:
1. **تحويل قاعدة بيانات Microsoft Access**:
   - دعم صيغ `.mdb`, `.accdb`, `.dblx`
   - تحويل تلقائي إلى JSON
   - ضغط الملف الناتج (gzip)
   - استخراج البيانات: الفئات، المنتجات، العملاء، الموردين، المبيعات

2. **إدارة ملفات التصدير**:
   - عرض قائمة الملفات المتاحة
   - تحميل مباشر للملفات
   - حذف الملفات غير المطلوبة
   - رابط تحميل عام (بدون مصادقة)

3. **استيراد البيانات إلى مشترك**:
   - اختيار ملف التصدير والمشترك المستهدف
   - خيار مسح البيانات الموجودة قبل الاستيراد
   - تسجيل عمليات الاستيراد في سجل
   - إحصائيات مفصلة بعد الاستيراد

#### API Endpoints الجديدة:
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/saas/database/exports` | GET | SuperAdmin | قائمة ملفات التصدير |
| `/api/saas/database/download/{filename}` | GET | SuperAdmin | تحميل ملف |
| `/api/saas/database/exports/{filename}` | DELETE | SuperAdmin | حذف ملف |
| `/api/saas/database/convert-access` | POST | SuperAdmin | تحويل ملف Access |
| `/api/saas/database/import/{tenant_id}` | POST | SuperAdmin | استيراد لمشترك |
| `/api/saas/database/import-logs` | GET | SuperAdmin | سجل الاستيراد |

#### الملفات المنشأة/المعدلة:
- `/app/backend/routes/database_routes.py` - Routes جديدة (350 سطر)
- `/app/backend/scripts/convert_access_db.py` - سكريبت التحويل (280 سطر)
- `/app/frontend/src/components/DatabaseManager.js` - تحديث الواجهة

#### ملف التصدير المتاح:
- **اسم الملف**: `BDV10_export.json.gz`
- **الحجم**: 2.08 MB (مضغوط)
- **المحتوى**: 82 فئة، 6,987 منتج، 121 عميل، 100 مورد، 31,624 عملية بيع
- **رابط التحميل**: `https://data-archive-5.preview.emergentagent.com/api/static/downloads/BDV10_export.json.gz`

## Updates (Feb 15, 2026 - Session 2)

### 1. فتح/غلق الحصة من POS مباشرة ✅ (NEW)
- **الميزة**: إضافة شريط معلومات الحصة في صفحة POS
- **المحتوى**:
  - عرض كود الحصة الحالية
  - عرض إحصائيات مباشرة (نقدي، دين، إجمالي، عدد العمليات)
  - زر "التفاصيل" لعرض كافة تفاصيل الحصة
  - زر "غلق الحصة" لغلقها مباشرة من POS
  - زر "فتح حصة" عندما لا توجد حصة مفتوحة
- **الملف المعدل**: `/app/frontend/src/pages/POSPage.js`

### 2. التحقق من حسابات "إجمالي النقد" ✅
- **النتيجة**: الحساب صحيح
- **الطريقة**: `total_cash = sum(balance for all cash_boxes)`
- يجمع أرصدة جميع الصناديق: النقدي، البنكي، المحفظة الإلكترونية، الخزنة

### 3. فحص اللغة الفرنسية ✅
- **النتيجة**: تعمل بشكل ممتاز
- **صفحة إضافة منتج**: جميع الحقول مترجمة (Nom du produit, Prix d'achat, Prix de gros, etc.)
- **رسالة النجاح**: "Produit ajouté avec succès"
- **لوحة التحكم**: Tableau de bord, Ventes du jour, Total caisse, etc.

### 4. نسخ/استعادة قاعدة البيانات للمشترك ✅
- **الميزة**: موجودة بالفعل في `/app/frontend/src/components/BackupSystem.js`
- **الوظائف**:
  - تصدير JSON/CSV
  - استيراد من JSON
  - إعدادات النسخ التلقائي
  - تحديد تكرار النسخ (يومي/أسبوعي/شهري)

## Recent Fixes (Feb 14, 2026 - Session 2)

### 1. إصلاح المساعد الذكي (AI Assistant) ✅
- **المشكلة**: كان يظهر مرتين في صفحة SaaS Admin
- **الحل**: إزالة المكون من `Layout.js` (كان يظهر لجميع الصفحات) وإبقاؤه فقط في تاب SaaS Admin
- **النتيجة**: المساعد الذكي يظهر فقط للمدير الأعلى في تاب مخصص

### 2. إزالة شارة "Made with Emergent" ✅
- **الحل**: إزالة الكود من `/app/frontend/public/index.html`
- **النتيجة**: لم تعد الشارة تظهر في أسفل يمين الصفحة

### 3. إصلاح حقل "الموديلات المتوافقة" ✅
- **المشكلة**: كان يضيف تلقائياً حروف اسم المنتج (c, ca, cab, cabl, cable)
- **الحل**: إزالة useEffect من `AddProductPage.js` الذي كان يضيف الحروف تلقائياً
- **النتيجة**: الحقل يبقى فارغاً والمستخدم يضيف ما يريد يدوياً

## Test Credentials
- **Super Admin**: `admin@ntcommerce.com` / `Admin@2024`
- **Tenant**: `ncr@ntcommerce.com` / `Test@123`

## Test Files
- `/app/backend/tests/test_pos_redesign.py` - اختبارات POS redesign (6 tests - all passing)
- `/app/test_reports/iteration_50.json` - Frontend tests for POS task menu (12 tests - all passing)
- `/app/test_reports/iteration_52.json` - اختبارات دعم الباركود وصفحة POS (100% success)

---
*Last Updated: February 15, 2026*
