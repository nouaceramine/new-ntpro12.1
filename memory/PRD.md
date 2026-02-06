# ScreenGuard Pro - PRD

## Original Problem Statement
تطبيق ويب لإدارة منتجات زجاج حماية الهواتف النقالة - إضافة المنتجات والبحث عنها ومعرفة الموديلات المتوافقة

## User Personas
1. **المدير (Admin)**: يمكنه إضافة/تعديل/حذف المنتجات وعرض الإحصائيات
2. **المستخدم العادي (User)**: يمكنه البحث وعرض المنتجات فقط

## Core Requirements (Static)
- نظام تسجيل دخول مع صلاحيات (مدير/مستخدم)
- معلومات المنتج: اسم، موديلات متوافقة، سعر، كمية، صورة، وصف
- البحث باسم المنتج أو موديل الهاتف
- دعم اللغة العربية والإنجليزية (RTL)
- تصميم بسيط وعملي

## What's Been Implemented (Jan 2026)
### Backend (FastAPI + MongoDB)
- ✅ نظام المصادقة JWT (تسجيل/دخول/خروج)
- ✅ CRUD كامل للمنتجات مع 3 أسعار (شراء، جملة، تجزئة)
- ✅ البحث بالاسم أو موديل الهاتف أو الباركود
- ✅ إدارة الزبائن (إضافة/تعديل/حذف + رصيد)
- ✅ إدارة الموردين (إضافة/تعديل/حذف + رصيد)
- ✅ نظام المبيعات (فواتير + خصومات + طرق دفع متعددة)
- ✅ نظام المشتريات من الموردين
- ✅ إدارة الصناديق (نقدي + بنكي + محفظة إلكترونية)
- ✅ تحويل الأموال بين الصناديق
- ✅ إرجاع المبيعات
- ✅ تنبيهات المخزون المنخفض
- ✅ تنبيهات إعادة التخزين
- ✅ فواتير PDF/HTML
- ✅ OCR لاستخراج الموديلات (Gemini)

### Frontend (React + Tailwind + Shadcn)
- ✅ لوحة تحكم شاملة مع إحصائيات
- ✅ واجهة نقطة البيع (POS) متقدمة
- ✅ إدارة المنتجات (إضافة/تعديل/حذف)
- ✅ إدارة الزبائن
- ✅ إدارة الموردين (للمدير)
- ✅ سجل المبيعات مع طباعة الفواتير
- ✅ إدارة المال والصناديق
- ✅ إدارة المستخدمين
- ✅ نظام الإشعارات
- ✅ دعم كامل للعربية (RTL)
- ✅ العملة: دينار جزائري (دج)

## Prioritized Backlog
### P0 (Critical) - Done
- [x] Authentication system
- [x] Product CRUD with 3 prices
- [x] POS system with discounts
- [x] Multiple payment methods
- [x] Cash boxes management
- [x] Customers & Suppliers
- [x] Sales history & returns
- [x] Invoice PDF
- [x] Notifications system

### P1 (High Priority)
- [ ] Barcode scanner integration
- [ ] Detailed financial reports
- [ ] Import/Export products (Excel)
- [ ] Email notifications

### P2 (Medium Priority)
- [ ] Dashboard charts
- [ ] Sales analytics
- [ ] Profit margin reports
- [ ] Backup & restore

## Next Tasks
1. إضافة ميزة تحميل الصور مباشرة
2. إضافة تصنيفات للمنتجات
3. تصدير واستيراد المنتجات (Excel/CSV)
