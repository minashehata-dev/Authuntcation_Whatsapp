# 🔐 نظام التحقق عبر الواتساب (WhatsApp OTP Backend)

نظام متكامل واحترافي مبني بلغة **Python (FastAPI)** و **Node.js (Baileys WhatsApp Web)** لإرسال رموز التحقق المؤقتة (OTP) إلى أرقام الهواتف عبر الواتساب بتنسيق جذاب ومحمي بنظام تشفير وتوقيع رقمي متقدم (**HMAC-SHA256**) لمنع التلاعب وتأمين الاتصال بين منصتك والباك إند.

---

## 🏛️ معمارية النظام (System Architecture)

```
┌─────────────────┐       طلب موثّق مشفّر (X-Signature + X-Timestamp)       ┌────────────────────────┐
│ منصتك / التطبيق │ ───────────────────────────────────────────────────────► │ Python Backend         │
│ (Web / Mobile)  │                                                          │ (FastAPI Port: 8000)   │
└─────────────────┘                                                          └───────────┬────────────┘
                                                                                         │
                                     توليد OTP آمن وتنسيق الرسالة الجذابة ───────────────┤
                                                                                         ▼
                                                                             ┌────────────────────────┐
                                    إرسال الرسالة عبر منفذ داخلي محمي         │ Baileys Gateway        │
                                    (X-Internal-Token)                       │ (Node.js Port: 3001)   │
                                                                             └───────────┬────────────┘
                                                                                         │
                                         بروتوكول WhatsApp Web WebSocket                 │
                                                                                         ▼
                                                                             ┌────────────────────────┐
                                                                             │  هاتف المستلم (واتساب) │
                                                                             └────────────────────────┘
```

---

## ✨ المميزات الرئيسية

1. **حماية الترويسة والتشفير (Cryptographic Header Verification):**
   - يدعم التحقق من التوقيع الرقمي **HMAC-SHA256** على كامل محتوى الطلب (`X-Signature`).
   - حماية ضد هجمات إعادة الإرسال (Replay Attacks) عبر الختم الزمني (`X-Timestamp`).
   - إمكانية تفعيل الـ `X-API-Key` الثابت أو الجمع بينهما.
2. **توليد وإدارة الـ OTP بأمان عالي:**
   - توليد كود رقمي عشوائي مشفر بالـ `secrets` في بايثون.
   - تحديد وقت انتهاء الصلاحية (مثلاً 5 دقائق).
   - حماية من الإغراق والتكرار (Rate Limiting & Cooldown) مثل الانتظار 60 ثانية قبل إعادة الإرسال لنفس الرقم.
   - حد أقصى للمحاولات الخاطئة (Brute-force protection) لمنع التخمين.
3. **تنسيق جذاب واحترافي لرسائل الواتساب:**
   - تصميم منسق بالإيموجي والفواصل الأنيقة والخط العريض.
   - كتابة الكود بشكل متباعد ومميز يسهل قراءته ونسخه.
   - تحذير أمني بعدم مشاركة الكود مع أي شخص.
   - دعم كامل للغتين (العربية والإنجليزية).
4. **بوابة Baileys مستقلة ومستقرة:**
   - حفظ جلسة الواتساب تلقائياً في مجلد `sessions/baileys_auth` لعدم الحاجة لمسح QR كل مرة.
   - عرض رمز الـ QR مباشرة في سطر الأوامر (Terminal) أو عبر صفحة ويب تفاعلية سهلة الفحص (`http://localhost:3001/api/qr`).
   - معالجة تلقائية لانقطاع الاتصال وإعادة الاتصال الذكي.

---

## 📁 هيكل المشروع

```
Authuntcation_Whatsapp/
├── backend/                  # سيرفر الباك إند بايثون (FastAPI)
│   ├── app/
│   │   ├── main.py           # نقاط الـ API والـ Endpoints الرئيسية
│   │   ├── config.py         # الإعدادات وقراءة متغيرات البيئة
│   │   ├── security.py       # دوال التشفير والتحقق من التوقيع الرقمي HMAC
│   │   ├── otp_service.py    # منطق توليد وتخزين والتحقق من أكواد OTP
│   │   ├── message_builder.py# صياغة وتنسيق رسالة الواتساب الجذابة
│   │   ├── whatsapp_client.py# عميل الاتصال ببوابة Baileys وتنسيق الأرقام
│   │   └── models.py         # نماذج البيانات (Pydantic Schemas)
│   ├── requirements.txt      # مكتبات البايثون
│   ├── test_suite.py         # اختبارات الوحدة الشاملة
│   └── .env                  # إعدادات الباك إند
├── whatsapp_gateway/         # بوابة الواتساب Baileys (Node.js)
│   ├── src/
│   │   ├── index.js          # سيرفر Express وإدارة الطلبات الداخلية
│   │   ├── whatsapp.js       # ربط مكتبة Baileys وحفظ الجلسة
│   │   └── config.js         # إعدادات البوابة
│   ├── package.json          # حزم Node.js
│   └── .env                  # إعدادات البوابة
├── run_services.py           # سكربت بايثون لتشغيل السيرفرين معاً بأمر واحد
├── start.bat                 # ملف تشغيل سريع لنظام Windows
└── test_client.py            # نموذج لمحاكاة إرسال طلب موقع من المنصة
```

---

## 🚀 طريقة التثبيت والتشغيل

### الخطوة 1: تشغيل السيرفرات

يمكنك تشغيل كلا السيرفرين (FastAPI + Baileys Gateway) معاً عبر:

**في نظام Windows (ضغطة زر واحدة):**
انقر مرتين على:
```cmd
start.bat
```
أو من موجه الأوامر:
```bash
py run_services.py
# أو
python run_services.py
```

### الخطوة 2: ربط رقم الواتساب (Scan QR Code)

عند أول تشغيل، سيظهر لك رمز QR للواتساب في شاشة الأوامر (Terminal)، كما يمكنك فتحه مباشرة من المتصفح عبر الرابط:
👉 **[http://localhost:3001/api/qr](http://localhost:3001/api/qr)**

1. افتح تطبيق الواتساب على هاتفك.
2. اضغط على **الأجهزة المرتبطة (Linked Devices)**.
3. اضغط على **ربط جهاز (Link a Device)** وامسح الرمز.
4. بمجرد المسح ستظهر رسالة `WHATSAPP CONNECTED SUCCESSFULLY!` وسيتم حفظ الجلسة محلياً.

---

## 🛡️ كيفية التشفير والتحقق من الـ Header (X-Signature)

لحماية الـ API من أي استدعاء غير مصرح به أو التلاعب بالبيانات، يجب على المنصة إرسال الترويسات التالية مع كل طلب `POST`:

| اسم الترويسة (Header) | الوصف | مثال |
|---|---|---|
| `X-Timestamp` | الطابع الزمني بالثواني (Unix Timestamp) | `1731172800` |
| `X-Signature` | توقيع **HMAC-SHA256** المحسوب على `Timestamp` + `.` + محتوى الطلب الخام | `a3b8f1c...` |
| `X-API-Key` | مفتاح المنصة السري (اختياري بحسب `SECURITY_MODE`) | `platform-api-key-9876543210` |

### معادلة حساب التوقيع الرقمي:
$$\text{Signature} = \text{HMAC-SHA256}(\text{SecretKey}, \text{Timestamp} + "." + \text{RawBody})$$

---

### أمثلة استدعاء الـ API من منصتك:

#### 1. كود Python:
```python
import hmac
import hashlib
import time
import json
import requests

SECRET_KEY = "super-secret-hmac-key-change-in-production-123456"
payload = {
    "phone_number": "01012345678", # يدعم الأرقام المحلية والدولية
    "user_name": "أحمد محمود",
    "purpose": "تسجيل الدخول"
}

body_bytes = json.dumps(payload).encode("utf-8")
timestamp = str(int(time.time()))
signature = hmac.new(
    SECRET_KEY.encode("utf-8"),
    f"{timestamp}.".encode("utf-8") + body_bytes,
    hashlib.sha256
).hexdigest()

headers = {
    "Content-Type": "application/json",
    "X-Signature": signature,
    "X-Timestamp": timestamp
}

response = requests.post("http://127.0.0.1:8000/api/v1/otp/send", data=body_bytes, headers=headers)
print(response.json())
```

#### 2. كود Node.js / JavaScript:
```javascript
const crypto = require('crypto');
const axios = require('axios');

const SECRET_KEY = "super-secret-hmac-key-change-in-production-123456";
const payload = {
    phone_number: "01012345678",
    user_name: "أحمد محمود",
    purpose: "تأكيد الحساب"
};

const rawBody = JSON.stringify(payload);
const timestamp = Math.floor(Date.now() / 1000).toString();

const signature = crypto
    .createHmac('sha256', SECRET_KEY)
    .update(`${timestamp}.${rawBody}`)
    .digest('hex');

axios.post('http://127.0.0.1:8000/api/v1/otp/send', payload, {
    headers: {
        'Content-Type': 'application/json',
        'X-Signature': signature,
        'X-Timestamp': timestamp
    }
}).then(res => console.log(res.data))
  .catch(err => console.error(err.response?.data || err.message));
```

#### 3. كود PHP:
```php
<?php
$secretKey = "super-secret-hmac-key-change-in-production-123456";
$data = [
    "phone_number" => "01012345678",
    "user_name" => "أحمد محمود",
    "purpose" => "تسجيل الدخول"
];

$rawBody = json_encode($data);
$timestamp = strval(time());
$signature = hash_hmac('sha256', "{$timestamp}.{$rawBody}", $secretKey);

$ch = curl_init("http://127.0.0.1:8000/api/v1/otp/send");
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, $rawBody);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    "X-Signature: {$signature}",
    "X-Timestamp: {$timestamp}"
]);

$response = curl_exec($ch);
curl_close($ch);
echo $response;
?>
```

---

## 🎨 شكل رسالة الواتساب الجذابة (Message Template)

تصل الرسالة إلى هاتف المستخدم بالتنسيق التالي:

```text
🔐 *كود التحقق السري (OTP)*
━━━━━━━━━━━━━━━━━━━━
مرحباً بك *أحمد محمود*،

طلب التحقق الخاص بـ *تسجيل الدخول*:

┌─────────────────────────┐
       👉   *749201*   👈
       ( 7  4  9  2  0  1 )
└─────────────────────────┘

⏳ هذا الرمز صالح لمدة *5 دقائق* فقط.
━━━━━━━━━━━━━━━━━━━━
⚠️ *تنبيه أمني هام:*
لا تشارك هذا الرمز مطلقاً مع أي شخص، حتى لو ادعى أنه من خدمة العملاء أو الدعم الفني. فريقنا لن يطلب منك هذا الرمز أبداً.
━━━━━━━━━━━━━━━━━━━━
✨ مع تحيات *منصة التوثيق الرسمية*
```

---

## 📡 نقاط الاتصال (API Endpoints)

| المسار (Endpoint) | الطريقة | الوصف |
|---|---|---|
| `POST /api/v1/otp/send` | `POST` | إرسال كود التحقق لرقم الهاتف (محمي بالـ Header) |
| `POST /api/v1/otp/verify` | `POST` | التحقق من صحة الكود المدخل بواسطة العميل |
| `GET /api/v1/whatsapp/status` | `GET` | فحص حالة اتصال الواتساب وجاهزيته |
| `GET /health` | `GET` | فحص الحالة العامة للنظام والسيرفرين |
| `GET /docs` | `GET` | واجهة توثيق وتجربة Swagger التفاعلية |

---

## ⚙️ إعدادات ملف البيئة (.env)

يمكنك تخصيص كافة المعايير في `backend/.env`:

```env
# المفتاح السري للتوقيع الرقمي (يجب تغييره في الإنتاج)
SECRET_KEY="your-production-hmac-secret-key"

# مدة صلاحية الكود بالثواني (300 ثانية = 5 دقائق)
OTP_EXPIRY_SECONDS=300

# عدد خانات الكود (افتراضياً 6)
OTP_LENGTH=6

# فترة الانتظار بين إعادة إرسال الكود لنفس الرقم (60 ثانية)
OTP_RESEND_COOLDOWN_SECONDS=60

# الحد الأقصى لمحاولات الإدخال الخاطئة قبل حرق الكود
OTP_MAX_VERIFY_ATTEMPTS=5

# اسم علامتك التجارية أو منصتك الظاهر في الرسالة
BRAND_NAME="اسم منصتك هنا"
```

---

## 🧪 تشغيل الاختبارات الذاتية

للتأكد من صحة دوال التشفير، دورة حياة الـ OTP، وتنسيق الأرقام:
```bash
py backend/test_suite.py
```
ستظهر لك النتيجة:
```
🧪 Running Unit Tests...
✅ test_normalization passed
✅ test_signature passed
✅ test_otp_lifecycle passed
✅ test_message_builder passed

🎉 ALL TESTS PASSED SUCCESSFULLY!
```
