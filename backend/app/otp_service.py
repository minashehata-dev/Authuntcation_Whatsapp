import sys
import os
import secrets
import time
import uuid
from typing import Dict, Any, Tuple, Optional
import threading

_app_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_app_dir)
for _p in [_backend_dir, _app_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from app.config import settings
except ImportError:
    from config import settings


class OTPStore:
    def __init__(self):
        # Format: {phone_number: {"code": str, "expires_at": float, "attempts": int, "last_sent_at": float, "request_id": str}}
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def generate_code(self, length: int) -> str:
        """Generates a cryptographically secure numeric OTP."""
        return "".join(secrets.choice("0123456789") for _ in range(length))

    def create_otp(self, phone_number: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        Creates an OTP for a phone number.
        Returns: (success, message, otp_code, request_id)
        """
        with self._lock:
            now = time.time()
            existing = self._store.get(phone_number)

            if existing:
                # Cooldown check
                elapsed = now - existing.get("last_sent_at", 0)
                if elapsed < settings.OTP_RESEND_COOLDOWN_SECONDS:
                    wait_remaining = int(settings.OTP_RESEND_COOLDOWN_SECONDS - elapsed)
                    return (
                        False,
                        f"يرجى الانتظار {wait_remaining} ثانية قبل طلب رمز جديد.",
                        None,
                        None
                    )

            # Generate new OTP
            code = self.generate_code(settings.OTP_LENGTH)
            request_id = str(uuid.uuid4())
            expires_at = now + settings.OTP_EXPIRY_SECONDS

            self._store[phone_number] = {
                "code": code,
                "expires_at": expires_at,
                "attempts": 0,
                "last_sent_at": now,
                "request_id": request_id
            }

            return True, "تم إنشاء الرمز بنجاح.", code, request_id

    def verify_otp(self, phone_number: str, entered_code: str) -> Tuple[bool, str]:
        """
        Verifies entered OTP against stored OTP.
        Returns: (verified, message)
        """
        with self._lock:
            now = time.time()
            record = self._store.get(phone_number)

            if not record:
                return False, "لم يتم العثور على رمز تحقق لهذا الرقم أو انتهت صلاحيته."

            # Expiration check
            if now > record["expires_at"]:
                del self._store[phone_number]
                return False, "انتهت صلاحية رمز التحقق، يرجى طلب رمز جديد."

            # Max attempts check
            record["attempts"] += 1
            if record["attempts"] > settings.OTP_MAX_VERIFY_ATTEMPTS:
                del self._store[phone_number]
                return False, "تم تجاوز الحد الأقصى لمحاولات التحقق، يرجى طلب رمز جديد."

            # Timing-safe comparison of OTP code
            if not secrets.compare_digest(record["code"], entered_code.strip()):
                remaining_attempts = settings.OTP_MAX_VERIFY_ATTEMPTS - record["attempts"]
                return (
                    False,
                    f"رمز التحقق غير صحيح. متبقي لديك {remaining_attempts} محاولة."
                )

            # Verification successful -> invalidate code
            del self._store[phone_number]
            return True, "تم التحقق من الرمز بنجاح!"

    def get_active_otp(self, phone_number: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._store.get(phone_number)


# Global singleton instance
otp_service = OTPStore()
