# NT Commerce - منصة محاسبة ذكية مدعومة بالذكاء الاصطناعي

## نظرة عامة
NT Commerce هي منصة محاسبة سحابية احترافية مدعومة بالذكاء الاصطناعي.

## المعمارية التقنية

### قاعدة البيانات
- **الاسم**: `ntbass` (تم إعادة التهيئة في 13 مارس 2026)
- **النوع**: MongoDB
- **المجموعات الرئيسية**: accounts, agent_tasks, ai_chat_history, ai_insights, audit_logs, cash_boxes, chat_sessions, currencies, currency_rate_history, users, subscriptions, payments, invoices, products, inventory, sales, expenses, reports, system_logs, error_logs, saas_tenants, saas_plans, tax_rates, settings
- **قواعد بيانات المستأجرين**: `tenant_{uuid}` لكل مستأجر

### البيئة
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="ntbass"
CORS_ORIGINS="*,https://nt-commerce.net,https://www.nt-commerce.net"
```

### النطاقات
- **Preview**: ai-accounting-mvp.preview.emergentagent.com
- **إنتاج**: nt-commerce.net (مخصص)

## بيانات الاختبار
- **مدير عام**: admin@ntcommerce.com / Admin@2024 (يفتح /saas-admin)
- **مستأجر**: ncr@ntcommerce.com / Test@123 (يفتح /tenant/dashboard)
- **Tenant ID**: 3d345aba-b832-4151-a2de-2554ce11c184
- **Tenant DB**: tenant_3d345aba_b832_4151_a2de_2554ce11c184

## الميزات المنجزة
- [x] إعادة تهيئة قاعدة البيانات (ntbass) - 13 مارس 2026
- [x] تكامل WhatsApp Business (MOCKED)
- [x] التقارير الضريبية (TVA, IRG, TAP)
- [x] العملات المتعددة (5 عملات)
- [x] نظام الإشعارات
- [x] تحسين الأداء
- [x] إصلاح تنسيق التاريخ (YYYY-MM-DD)
- [x] توحيد JWT secrets
- [x] إصلاح CORS للنطاق الجديد
- [x] إصلاح Pydantic validation errors (ProductResponse, PlanResponse)

## المهام القادمة (Backlog)
- [ ] تقسيم server.py (~11,700 سطر) إلى modules
- [ ] ربط WhatsApp مع Meta API الحقيقي
- [ ] إشعارات push (Service Worker)
- [ ] تطبيق PWA
- [ ] تكامل بنكي

## التكاملات
- **OpenAI GPT-4o**: عبر Emergent LLM Key
- **MongoDB**: ntbass (محلي)
- **Stripe**: مفتاح اختبار
- **WhatsApp Business API**: MOCKED

---
*آخر تحديث: 13 مارس 2026*
*الإصدار: 3.1 - Database Reset + Domain Migration*
