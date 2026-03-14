# NT Commerce - هيكل الملف server.py

## خريطة المسارات (11,900+ سطر)

### الأقسام الرئيسية:
| القسم | الأسطر | الوصف |
|-------|--------|-------|
| الاستيرادات والإعدادات | 1-200 | DB, JWT, middleware, robots |
| النماذج (Models) | 200-420 | Pydantic models |
| المساعدات (Helpers) | 420-710 | Hash, verify, JWT functions |
| المصادقة (Auth) | 710-960 | Login, register, /me, 2FA |
| إدارة المستخدمين | 960-1070 | CRUD users |
| المنتجات (Products) | 1070-1830 | Products CRUD, search, history |
| العملاء (Customers) | 1830-2070 | Customers CRUD, blacklist |
| التذكيرات والإشعارات | 2070-2280 | Debt reminders, notifications |
| المخازن | 2280-2360 | Warehouses, stock transfers |
| جلسات الجرد | 2360-2580 | Inventory sessions |
| تحديثات الأسعار | 2580-2750 | Price updates |
| الجلسات اليومية | 2750-2990 | Daily sessions (POS) |
| الصناديق | 2990-3350 | Cash boxes CRUD |
| موجز المالي | 3350-3780 | Financial summary, reports |
| المبيعات (Sales) | 3780-5200 | Sales CRUD, returns, pagination |
| الموردين | 5200-5400 | Suppliers CRUD |
| المشتريات | 5400-6120 | Purchases CRUD |
| المصروفات | 6120-6900 | Expenses CRUD |
| SMS & WhatsApp | 6900-7400 | SMS config, WhatsApp (mocked) |
| لوحة التحكم | 7400-7800 | Dashboard analytics |
| الإعدادات | 7800-8000 | Settings CRUD |
| الإحصائيات | 8000-8600 | Reports, analytics |
| البحث والتصدير | 8600-9200 | Search, data export |
| التقارير المتقدمة | 9200-9460 | Advanced sales reports |
| إعدادات النظام | 9460-9900 | Features, permissions, receipt |
| تحديثات النظام | 9900-10060 | System updates (super admin) |
| المزامنة | 10060-10230 | Sync system |
| إدارة قاعدة البيانات | 10230-10380 | Tenant DB management |
| البريد الإلكتروني | 10380-10570 | SendGrid notifications |
| المدفوعات (Stripe) | 10570-10930 | Stripe integration |
| المتجر الإلكتروني | 10930-11160 | Online store |
| المنتجات المعيبة | 11160-11440 | Defective products |
| مساعد AI | 11440-11580 | AI assistant for SaaS admin |
| التقارير التلقائية | 11580-11610 | Auto reports API |
| الروبوتات | 11650-11710 | Robot control endpoints |

### الملفات المستخرجة بالفعل:
- `routes/saas_routes.py` - إدارة SaaS
- `routes/database_routes.py` - استيراد/تصدير DB
- `routes/ai/chat_routes.py` - محادثة AI
- `routes/accounting/accounting_routes.py` - المحاسبة
- `routes/settings_routes.py` - الإعدادات
- `routes/whatsapp_routes.py` - WhatsApp
- `routes/tax_routes.py` - الضرائب
- `routes/notification_routes.py` - الإشعارات
- `routes/currency_routes.py` - العملات
- `routes/performance_routes.py` - الأداء
- `routes/banking_routes.py` - البنوك

### أولويات الاستخراج المستقبلية:
1. **Products** (~760 سطر) - الأكثر حجماً
2. **Sales** (~1400 سطر) - الأكثر تعقيداً
3. **Expenses/Purchases** (~800 سطر)
4. **Auth** (~250 سطر) - الأكثر حساسية
