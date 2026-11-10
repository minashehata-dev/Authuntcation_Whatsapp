import sys
import os
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.security import compute_signature
from app.otp_service import OTPStore
from app.message_builder import build_whatsapp_otp_message
from app.whatsapp_client import normalize_phone_number
from app.config import settings

def test_normalization():
    assert normalize_phone_number("01012345678") == "201012345678"
    assert normalize_phone_number("+201012345678") == "201012345678"
    assert normalize_phone_number("00201012345678") == "201012345678"
    assert normalize_phone_number("0501234567") == "966501234567"
    assert normalize_phone_number("+966501234567") == "966501234567"
    print("✅ test_normalization passed")

def test_signature():
    secret = "test-secret-key"
    ts = str(int(time.time()))
    body = b'{"phone_number":"201012345678"}'
    
    sig1 = compute_signature(secret, ts, body)
    sig2 = compute_signature(secret, ts, body)
    assert sig1 == sig2
    
    # Tampered body check
    sig_tampered = compute_signature(secret, ts, b'{"phone_number":"201099999999"}')
    assert sig1 != sig_tampered
    print("✅ test_signature passed")

def test_otp_lifecycle():
    store = OTPStore()
    phone = "201012345678"
    
    # Create OTP
    ok, msg, code, req_id = store.create_otp(phone)
    assert ok is True
    assert len(code) == 6
    assert code.isdigit()
    
    # Cooldown check
    ok2, msg2, code2, _ = store.create_otp(phone)
    assert ok2 is False
    assert "ثانية" in msg2

    # Wrong code check
    verified_wrong, wrong_msg = store.verify_otp(phone, "000000" if code != "000000" else "111111")
    assert verified_wrong is False
    assert "غير صحيح" in wrong_msg

    # Correct code check
    verified, ok_msg = store.verify_otp(phone, code)
    assert verified is True
    assert "بنجاح" in ok_msg

    # Code should now be consumed / invalidated
    verified_again, _ = store.verify_otp(phone, code)
    assert verified_again is False
    print("✅ test_otp_lifecycle passed")

def test_message_builder():
    msg_ar = build_whatsapp_otp_message(
        code="749201",
        user_name="مينا",
        purpose="تسجيل الدخول",
        locale="ar"
    )
    assert "749201" in msg_ar
    assert "مينا" in msg_ar
    assert "تنبيه أمني هام" in msg_ar

    msg_en = build_whatsapp_otp_message(
        code="749201",
        user_name="Mina",
        purpose="Login",
        locale="en"
    )
    assert "749201" in msg_en
    assert "Mina" in msg_en
    assert "SECURITY NOTICE" in msg_en
    print("✅ test_message_builder passed")

def main():
    print("🧪 Running Unit Tests...")
    test_normalization()
    test_signature()
    test_otp_lifecycle()
    test_message_builder()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
