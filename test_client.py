import hmac
import hashlib
import time
import json
import urllib.request
import urllib.error
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Backend API Configuration
BASE_URL = "http://127.0.0.1:8000"
SECRET_KEY = "super-secret-hmac-key-change-in-production-123456"
API_KEY = "platform-api-key-9876543210"


def send_signed_request(endpoint: str, data: dict):
    """
    Sends a POST request to the backend with encrypted / cryptographic HMAC-SHA256
    signature headers.
    """
    url = f"{BASE_URL}{endpoint}"
    body_bytes = json.dumps(data).encode("utf-8")
    
    # Generate timestamp
    timestamp = str(int(time.time()))
    
    # Calculate HMAC-SHA256 signature: hmac(secret, timestamp + "." + body)
    payload_to_sign = f"{timestamp}.".encode("utf-8") + body_bytes
    signature = hmac.new(
        key=SECRET_KEY.encode("utf-8"),
        msg=payload_to_sign,
        digestmod=hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature,
        "X-Timestamp": timestamp,
        "X-API-Key": API_KEY
    }

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            return response.status, json.loads(res_body)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(error_body)
        except Exception:
            return e.code, {"error": error_body}
    except Exception as e:
        return 0, {
            "error": "Connection failed",
            "details": str(e),
            "hint": "تأكد من تشغيل السيرفر أولاً عبر تشغيل start.bat أو python run_services.py"
        }


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing WhatsApp OTP Backend API with Cryptographic Headers")
    print("=" * 60)

    test_phone = "+201226833781"  # Replace with your test WhatsApp phone number

    # 1. Test Sending OTP
    print(f"\n1️⃣ Sending OTP to {test_phone}...")
    status_code, response = send_signed_request(
        endpoint="/api/v1/otp/send",
        data={
            "phone_number": test_phone,
            "user_name": "أحمد محمد",
            "purpose": "تسجيل الدخول للنظام",
            "locale": "ar"
        }
    )
    
    if status_code == 0:
        print("\n❌ تعذر الاتصال بالسيرفر:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        sys.exit(1)

    print(f"Status Code: {status_code}")
    print("Response:", json.dumps(response, indent=2, ensure_ascii=False))

    # 2. Test Invalid Signature (Tamper test)
    print("\n2️⃣ Testing Security Protection (Tampered Header)...")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/otp/send",
        data=json.dumps({"phone_number": test_phone}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Signature": "fake_invalid_tampered_signature_12345",
            "X-Timestamp": str(int(time.time())),
            "X-API-Key": API_KEY
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("Status:", resp.status)
    except urllib.error.HTTPError as e:
        print(f"✅ Security working! Rejected with status {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Could not connect: {e}")
