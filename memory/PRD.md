# NT Commerce - منصة محاسبة ذكية مدعومة بالذكاء الاصطناعي

## نظرة عامة
NT Commerce هي منصة SaaS متكاملة لإدارة المبيعات والمخزون والمحاسبة مع روبوتات ذكية تعمل تلقائياً 24/7.

## المعمارية التقنية

### Stack: FastAPI + MongoDB + React + Tailwind + Shadcn/UI
### قاعدة البيانات: `ntbass`

### Backend Architecture
```
/app/backend/
├── server.py              # الخادم الرئيسي (~11,900 سطر)
├── robots/                # 6 روبوتات ذكية
│   ├── robot_manager.py   # المدير المركزي
│   ├── inventory_robot.py # المخزون (ML predictions)
│   ├── debt_robot.py      # الديون والتحصيل
│   ├── report_robot.py    # التقارير (PDF + Email)
│   ├── customer_robot.py  # تحليل العملاء
│   ├── pricing_robot.py   # تحسين الأسعار
│   └── maintenance_robot.py # صيانة النظام
├── services/
│   ├── notification_service.py
│   ├── sms_service.py     # MOCKED
│   └── email_service.py   # SendGrid
├── routes/                # 11 ملف مسارات مستخرجة
├── utils/
│   ├── errors.py          # Password validation + AppException
│   └── pagination.py
├── tests/
│   ├── test_comprehensive.py  # 21 اختبار
│   ├── test_robots.py
│   └── test_auth.py
└── docs/
    ├── README.md
    └── CONTRIBUTING.md
```

## الميزات المنجزة

### الروبوتات الذكية (6 روبوتات)
| الروبوت | الوظيفة | الدورية |
|---------|---------|---------|
| المخزون | مراقبة + توصيات + توقع نفاد (ML) | كل ساعة |
| الديون | متابعة + تذكيرات SMS + تحليل تحصيل | كل 6 ساعات |
| التقارير | يومي/أسبوعي/شهري + PDF + Email | يومي |
| العملاء | تقسيم + VIP + غير نشطين | كل 12 ساعة |
| التسعير | هوامش ربح + بطيء البيع + توصيات | يومي |
| الصيانة | تنظيف + فهارس + صحة النظام | يومي |

### الأمان
- [x] Brute-force protection (5 محاولات → قفل 15 دقيقة)
- [x] 2FA/TOTP (إعداد + QR code + تفعيل/إلغاء)
- [x] JWT authentication
- [x] Rate Limiting (120 req/min)
- [x] CORS configured
- [x] Password validation utility

### الصفحات الجديدة (Frontend)
- [x] `/robots` - لوحة تحكم الروبوتات (6 بطاقات + تحكم)
- [x] `/auto-reports` - التقارير التلقائية (فلترة + تفاصيل)

### API Endpoints
```
# Robots
GET    /api/robots/status
POST   /api/robots/run/{name}
POST   /api/robots/restart/{name}
POST   /api/robots/stop-all
POST   /api/robots/start-all

# Auto Reports
GET    /api/auto-reports
GET    /api/auto-reports?report_type=daily|weekly|monthly
GET    /api/auto-reports/{report_id}
GET    /api/collection-reports

# 2FA
GET    /api/auth/2fa/status
POST   /api/auth/2fa/setup
POST   /api/auth/2fa/verify
POST   /api/auth/2fa/disable
```

## نتائج الاختبارات
- pytest: 21/21 ✅ (test_comprehensive.py)
- Testing Agent #62: Backend 22/22, Frontend All passed ✅

## بيانات الاختبار
- **مدير عام**: admin@ntcommerce.com / Admin@2024
- **مستأجر**: ncr@ntcommerce.com / Test@123

## MOCKED Services
- SMS Service (سجل فقط)
- Email Service (إذا لم يتوفر مفتاح SendGrid)
- WhatsApp Integration

## المهام المتبقية

### P1 - أولوية عالية
- [ ] تقسيم server.py (خريطة جاهزة في route_index.md)
- [ ] واجهة 2FA في الفرونت إند

### P2 - أولوية متوسطة
- [ ] ربط SMS بمزود حقيقي (Twilio)
- [ ] ربط WhatsApp بـ Meta API
- [ ] إشعارات push حقيقية عبر Service Worker

### P3 - أولوية منخفضة
- [ ] استيراد بيانات Access
- [ ] تكامل بنكي حقيقي

---
*آخر تحديث: 14 مارس 2026*
*الإصدار: 6.0 - Full Robot Fleet + Security + Reports*
