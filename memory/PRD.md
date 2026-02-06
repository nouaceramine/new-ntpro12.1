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
- ✅ CRUD كامل للمنتجات
- ✅ البحث بالاسم أو موديل الهاتف (يشمل الموديلات المتوافقة)
- ✅ حماية الصلاحيات (Admin only endpoints)
- ✅ إحصائيات لوحة التحكم
- ✅ إدارة المستخدمين (عرض/تعديل/حذف)
- ✅ تنبيهات المخزون المنخفض (حد قابل للتخصيص)
- ✅ OCR لاستخراج الموديلات من الصور (Gemini)

### Frontend (React + Tailwind + Shadcn)
- ✅ صفحات تسجيل الدخول وإنشاء حساب
- ✅ لوحة التحكم مع الإحصائيات
- ✅ قائمة المنتجات مع البحث والفلترة
- ✅ صفحة تفاصيل المنتج
- ✅ نموذج إضافة/تعديل المنتج مع OCR
- ✅ صفحة إدارة المستخدمين
- ✅ دعم كامل للغة العربية (RTL)
- ✅ تبديل اللغة (عربي/إنجليزي)

## Prioritized Backlog
### P0 (Critical) - Done
- [x] Authentication system
- [x] Product CRUD
- [x] Search functionality
- [x] Bilingual support

### P1 (High Priority)
- [ ] Import/Export products (CSV/Excel)
- [ ] Product categories
- [ ] Image upload instead of URL
- [ ] Email notifications for low stock

### P2 (Medium Priority)
- [ ] Product barcode/QR support
- [ ] Sales tracking
- [ ] Customer management
- [ ] Reports and analytics

## Next Tasks
1. إضافة ميزة تحميل الصور مباشرة
2. إضافة تصنيفات للمنتجات
3. تصدير واستيراد المنتجات (Excel/CSV)
