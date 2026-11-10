import sys
import os
from typing import Optional

_app_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_app_dir)
for _p in [_backend_dir, _app_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from app.config import settings
except ImportError:
    from config import settings


def format_otp_code_display(code: str) -> str:
    """Formats code with spaces for easier reading (e.g. '8 5 4 1 2 0')."""
    return "  ".join(list(code))


def build_whatsapp_otp_message(
    code: str,
    user_name: Optional[str] = None,
    purpose: Optional[str] = None,
    locale: str = "ar"
) -> str:
    """
    Builds a beautifully styled WhatsApp message with emojis,
    clean dividers, clear OTP code, security warnings, and branding.
    """
    expiry_minutes = max(1, settings.OTP_EXPIRY_SECONDS // 60)
    brand = settings.BRAND_NAME
    spaced_code = format_otp_code_display(code)

    if locale.lower() == "en":
        greeting = f"Hello *{user_name}*," if user_name else "Hello,"
        purpose_line = f"Your verification code for *{purpose}* is:" if purpose else "Your verification code is:"
        
        message = (
            f"*VERIFICATION CODE*\n"
            f"{greeting}\n\n"
            f"{purpose_line}\n\n"
            f"*`{code}`*\n"
            f"Valid for *{expiry_minutes} minutes* only.\n"
            f"━━━━━━━━━━━━━\n"
            f"*SECURITY NOTICE:*\n"
            f"Do NOT share this code with anyone. Our support team will never ask for your verification code.\n"

            f"Sent via *{brand}*"
        )
    else:
        # Arabic template (Default)
        greeting = f"مرحباً بك *{user_name}*،" if user_name else "مرحباً بك عزيزنا العميل،"
        purpose_line = f"طلب التحقق الخاص بـ *{purpose}*:" if purpose else "رمز التحقق السريع الخاص بك:"

        message = (
            f" *كود التحقق السري (OTP)*\n"
            f"{greeting}\n\n"
            f"*`{code}`*\n"
            f" صلاحية الرمز: *{expiry_minutes} دقائق فقط*\n"
            f" *تنبيه أمني هام:*\n"
            f"لا تشارك هذا الرمز مطلقاً مع أي شخص، حتى لو ادعى أنه من الدعم الفني. فريقنا لن يطلب منك هذا الرمز أبداً.\n"
            f"──────────\n"
            f"*{brand}*"
        )

    return message
