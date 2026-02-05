# 🏥 KSAR - نظام إدارة طلبات المساعدة

<div dir="rtl">

نظام متكامل لإدارة طلبات المساعدة الإنسانية، يُمكّن المواطنين من التسجيل وتقديم طلباتهم، ويُتيح للمؤسسات الخيرية التكفل بها ومتابعتها حتى الإتمام.

</div>

---

## 📋 نظرة عامة

| الميزة | الوصف |
|--------|-------|
| 👤 **تسجيل المواطنين** | يُسجل المواطنون حساباتهم لتقديم الطلبات |
| 🏢 **إدارة المؤسسات** | المؤسسات الخيرية تتكفل بالطلبات |
| 📊 **لوحة تحكم إدارية** | مراقبة شاملة مع تحليلات |
| 📍 **دعم الإحداثيات** | تحديد مواقع المستفيدين |
| 🔒 **مصادقة JWT** | نظام أمان متكامل |
| 📱 **متابعة الطلبات** | يتابع المواطن حالة طلباته |

---

## 🚀 التشغيل السريع

### المتطلبات
- Docker & Docker Compose
- Git

### التثبيت

```bash
# استنساخ المشروع
git clone https://github.com/geniustep/ksar-backend.git
cd ksar-backend

# نسخ ملف الإعدادات
cp backend/.env.example backend/.env

# تشغيل الخدمات
docker-compose up -d

# إنشاء قاعدة البيانات والمستخدم الافتراضي
docker exec ksar-backend python scripts/init_db.py
```

### التحقق من التشغيل

```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"ksar-backend","version":"2.0.0"}
```

---

## 🔑 بيانات الدخول الافتراضية

| الدور | البريد الإلكتروني | كلمة المرور |
|-------|------------------|-------------|
| 👨‍💼 الإدارة | `admin@ksar.ma` | `admin123` |
| 🏢 المؤسسة | `org@ksar.ma` | `org123` |
| 👤 المواطن | `citizen@example.ma` | `citizen123` |

> ⚠️ **تنبيه**: يُرجى تغيير كلمات المرور فور التشغيل في بيئة الإنتاج

---

## 📚 توثيق API

### الوثائق التفاعلية
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔄 تدفق العمل

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    المواطن      │────▶│    الإدارة      │────▶│    المؤسسة     │
│ يُسجل ويُقدم   │     │  تراقب وتوجه   │     │ تتكفل وتُنجز   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
  [تسجيل + طلب]         [مراقبة + تحليل]        [تكفل + إتمام]
        │                                               │
        └───────────── [متابعة الحالة] ◀───────────────┘
```

---

## 📡 المسارات الرئيسية (API Endpoints)

### 🌐 المسارات العامة (بدون مصادقة)

#### متابعة الطلب (بدون تسجيل)
```http
GET /api/v1/public/requests/track/{tracking_code}?phone=0612345678
```

#### عرض أنواع الطلبات
```http
GET /api/v1/public/categories
```

---

### 🔐 المصادقة

#### تسجيل مواطن جديد
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.ma",
  "password": "password123",
  "full_name": "أحمد محمد",
  "phone": "0612345678",
  "address": "حي السلام، زقاق 3",
  "city": "الدار البيضاء",
  "region": "حي السلام"
}
```

**الاستجابة:**
```json
{
  "message": "تم إنشاء الحساب بنجاح. يمكنك الآن تقديم طلباتك.",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.ma",
    "full_name": "أحمد محمد",
    "role": "citizen"
  }
}
```

#### تسجيل الدخول
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.ma",
  "password": "password123"
}
```

#### تجديد التوكن
```http
POST /api/v1/auth/refresh
Authorization: Bearer {token}
```

#### الملف الشخصي
```http
GET /api/v1/auth/me
Authorization: Bearer {token}
```

#### تحديث الملف الشخصي
```http
PATCH /api/v1/auth/me
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "أحمد محمد العلوي",
  "address": "حي الفردوس، رقم 5"
}
```

---

### 👤 مسارات المواطنين

> تتطلب جميع المسارات توكن مصادقة بدور `citizen`

#### تقديم طلب جديد
```http
POST /api/v1/citizen/requests
Authorization: Bearer {citizen_token}
Content-Type: application/json

{
  "category": "food",
  "description": "نحتاج مواد غذائية لأسرة مكونة من 5 أفراد",
  "quantity": 1,
  "family_members": 5,
  "is_urgent": false
}
```

**ملاحظة:** إذا لم تُحدد العنوان، يُستخدم العنوان المحفوظ في الملف الشخصي.

**الاستجابة:**
```json
{
  "id": "uuid",
  "tracking_code": "ABC12345",
  "message": "تم استلام طلبك بنجاح. رمز المتابعة: ABC12345"
}
```

#### عرض طلباتي
```http
GET /api/v1/citizen/requests?status=new
Authorization: Bearer {citizen_token}
```

#### تفاصيل طلب
```http
GET /api/v1/citizen/requests/{request_id}
Authorization: Bearer {citizen_token}
```

#### تعديل طلب (قبل التكفل فقط)
```http
PATCH /api/v1/citizen/requests/{request_id}
Authorization: Bearer {citizen_token}
Content-Type: application/json

{
  "description": "تعديل الوصف",
  "family_members": 6,
  "is_urgent": true
}
```

#### إلغاء طلب (قبل التكفل فقط)
```http
DELETE /api/v1/citizen/requests/{request_id}
Authorization: Bearer {citizen_token}
```

#### إحصائياتي
```http
GET /api/v1/citizen/stats
Authorization: Bearer {citizen_token}
```

**الاستجابة:**
```json
{
  "total_requests": 5,
  "by_status": {
    "new": 1,
    "assigned": 2,
    "completed": 2
  }
}
```

---

### 👨‍💼 مسارات الإدارة

> تتطلب جميع المسارات توكن مصادقة بدور `admin`

#### عرض جميع الطلبات
```http
GET /api/v1/admin/requests?status=new&category=food&page=1&limit=20
Authorization: Bearer {admin_token}
```

**معاملات التصفية:**
| المعامل | الوصف | القيم |
|---------|-------|-------|
| `status` | حالة الطلب | `new`, `assigned`, `in_progress`, `completed`, `cancelled` |
| `category` | نوع الطلب | `food`, `medicine`, `shelter`, `clothing`, `blankets`, `financial`, `other` |
| `region` | المنطقة | نص حر |
| `is_urgent` | الطلبات المستعجلة | `true`, `false` |
| `date_from` | من تاريخ | `YYYY-MM-DD` |
| `date_to` | إلى تاريخ | `YYYY-MM-DD` |

#### تفاصيل طلب
```http
GET /api/v1/admin/requests/{request_id}
Authorization: Bearer {admin_token}
```

#### تحديث طلب
```http
PATCH /api/v1/admin/requests/{request_id}
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "status": "cancelled",
  "admin_notes": "تم إلغاء الطلب بناءً على طلب المستفيد"
}
```

#### حذف طلب
```http
DELETE /api/v1/admin/requests/{request_id}
Authorization: Bearer {admin_token}
```

---

### 📊 الإحصائيات (للإدارة)

#### نظرة عامة
```http
GET /api/v1/admin/stats/overview
Authorization: Bearer {admin_token}
```

**الاستجابة:**
```json
{
  "data": {
    "total_requests": 150,
    "by_status": {
      "new": 25,
      "assigned": 40,
      "in_progress": 30,
      "completed": 50,
      "cancelled": 5
    },
    "by_category": {
      "food": 80,
      "medicine": 30,
      "clothing": 40
    },
    "urgent_count": 12,
    "avg_completion_hours": 48.5,
    "active_organizations": 8
  }
}
```

#### إحصائيات يومية
```http
GET /api/v1/admin/stats/daily?days=30
Authorization: Bearer {admin_token}
```

#### إحصائيات حسب المنطقة
```http
GET /api/v1/admin/stats/by-region
Authorization: Bearer {admin_token}
```

#### إحصائيات المؤسسات
```http
GET /api/v1/admin/stats/organizations
Authorization: Bearer {admin_token}
```

---

### 🏢 إدارة المؤسسات

#### عرض جميع المؤسسات
```http
GET /api/v1/admin/organizations
Authorization: Bearer {admin_token}
```

#### تحديث حالة مؤسسة
```http
PATCH /api/v1/admin/organizations/{org_id}/status
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "is_active": true
}
```

---

### 🏢 مسارات المؤسسات

> تتطلب جميع المسارات توكن مصادقة بدور `organization`

#### عرض الطلبات المتاحة
```http
GET /api/v1/org/requests/available?category=food&region=الدار البيضاء
Authorization: Bearer {org_token}
```

#### تفاصيل طلب متاح
```http
GET /api/v1/org/requests/{request_id}
Authorization: Bearer {org_token}
```

#### التكفل بطلب
```http
POST /api/v1/org/assignments
Authorization: Bearer {org_token}
Content-Type: application/json

{
  "request_id": "uuid",
  "notes": "سنتواصل مع المستفيد غداً"
}
```

#### عرض تكفلاتي
```http
GET /api/v1/org/assignments?status=pledged
Authorization: Bearer {org_token}
```

#### تفاصيل تكفل
```http
GET /api/v1/org/assignments/{assignment_id}
Authorization: Bearer {org_token}
```

#### تحديث حالة التكفل
```http
PATCH /api/v1/org/assignments/{assignment_id}
Authorization: Bearer {org_token}
Content-Type: application/json

{
  "status": "completed",
  "completion_notes": "تم تسليم المواد للأسرة بنجاح"
}
```

**حالات التكفل:**
| الحالة | الوصف |
|--------|-------|
| `pledged` | تم التكفل (الحالة الأولية) |
| `in_progress` | قيد التنفيذ |
| `completed` | تم الإتمام |
| `failed` | فشل التنفيذ |

#### إحصائيات مؤسستي
```http
GET /api/v1/org/stats
Authorization: Bearer {org_token}
```

---

## 📦 أنواع الطلبات

| النوع | الرمز | الوصف |
|-------|-------|-------|
| 🍞 مواد غذائية | `food` | مواد غذائية أساسية |
| 💊 أدوية | `medicine` | أدوية ومستلزمات طبية |
| 🏠 مأوى | `shelter` | سكن مؤقت أو دائم |
| 👕 ملابس | `clothing` | ملابس وأحذية |
| 🛏️ أغطية | `blankets` | بطانيات وأفرشة |
| 💰 مساعدة مالية | `financial` | دعم مادي |
| 📦 أخرى | `other` | طلبات متنوعة |

---

## 🗄️ هيكل قاعدة البيانات

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    users     │     │   requests   │     │ organizations│
├──────────────┤     ├──────────────┤     ├──────────────┤
│ id           │     │ id           │     │ id           │
│ email        │◀────│ user_id (FK) │     │ name         │
│ password_hash│     │ category     │     │ user_id (FK) │
│ full_name    │     │ description  │     │ contact_*    │
│ phone        │     │ status       │     │ is_active    │
│ address      │     │ priority     │     │ total_done   │
│ city/region  │     │ address      │     └──────────────┘
│ role         │     │ is_urgent    │
└──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ assignments  │
                     ├──────────────┤
                     │ id           │
                     │ request_id   │
                     │ org_id       │
                     │ status       │
                     │ notes        │
                     └──────────────┘
```

### الأدوار (Roles)

| الدور | الوصف | الصلاحيات |
|-------|-------|----------|
| `admin` | الإدارة | إدارة كاملة للنظام |
| `organization` | المؤسسة | التكفل بالطلبات وإتمامها |
| `citizen` | المواطن | تقديم ومتابعة الطلبات |

---

## 🐳 Docker

### الخدمات

| الخدمة | المنفذ | الوصف |
|--------|--------|-------|
| `ksar-backend` | 8000 | خادم FastAPI |
| `ksar-db` | 5432 | قاعدة بيانات PostgreSQL |
| `ksar-redis` | 6379 | ذاكرة التخزين المؤقت |

### أوامر مفيدة

```bash
# عرض السجلات
docker logs -f ksar-backend

# إعادة تشغيل الخدمات
docker-compose restart

# إعادة بناء الصورة
docker-compose up -d --build

# الدخول للحاوية
docker exec -it ksar-backend bash

# إعادة تهيئة قاعدة البيانات
docker exec ksar-backend python scripts/init_db.py
```

---

## ⚙️ متغيرات البيئة

```env
# قاعدة البيانات
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0

# الأمان
SECRET_KEY=your-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# التطبيق
APP_NAME=KSAR
DEBUG=false
```

---

## 🏗️ هيكل المشروع

```
ksar-backend/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── admin.py      # مسارات الإدارة
│   │   │   │   ├── auth.py       # المصادقة
│   │   │   │   ├── organizations.py  # المؤسسات
│   │   │   │   └── public.py     # المسارات العامة
│   │   │   ├── deps.py           # التبعيات
│   │   │   └── router.py         # تجميع المسارات
│   │   ├── core/
│   │   │   ├── constants.py      # الثوابت
│   │   │   └── security.py       # الأمان
│   │   ├── models/               # نماذج قاعدة البيانات
│   │   ├── schemas/              # مخططات Pydantic
│   │   ├── config.py             # الإعدادات
│   │   ├── database.py           # اتصال قاعدة البيانات
│   │   └── main.py               # نقطة الدخول
│   ├── scripts/
│   │   └── init_db.py            # تهيئة قاعدة البيانات
│   ├── requirements.txt
│   └── .env
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 🔒 الأمان

- ✅ تشفير كلمات المرور بـ bcrypt
- ✅ مصادقة JWT مع انتهاء صلاحية
- ✅ التحقق من الأدوار (RBAC)
- ✅ التحقق من صحة البيانات المدخلة
- ✅ حماية CORS

---

## 🛠️ التطوير

### تشغيل محلياً (بدون Docker)

```bash
cd backend

# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
.\venv\Scripts\activate   # Windows

# تثبيت التبعيات
pip install -r requirements.txt

# تشغيل الخادم
uvicorn app.main:app --reload --port 8000
```

---

## 📄 الترخيص

MIT License

---

## 👥 المساهمة

نرحب بمساهماتكم! يرجى:
1. Fork المشروع
2. إنشاء فرع للميزة (`git checkout -b feature/amazing`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push للفرع (`git push origin feature/amazing`)
5. فتح Pull Request

---

## 📞 الدعم

للمساعدة أو الاستفسارات، يرجى فتح Issue في GitHub.

---

<div align="center">

**صُنع بـ ❤️ لخدمة المجتمع**

</div>
