import sys
import os
import httpx
from typing import Tuple, Dict, Any, Optional

_app_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_app_dir)
for _p in [_backend_dir, _app_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from app.config import settings
except ImportError:
    from config import settings


def normalize_phone_number(raw_phone: str) -> str:
    """
    Normalizes local/international numbers to international format digits:
    - Egypt: '01012345678' -> '201012345678'
    - Saudi: '0501234567' -> '966501234567'
    - International '+201012345678' -> '201012345678'
    """
    digits = "".join(c for c in raw_phone if c.isdigit())
    
    # Strip leading 00 if present
    if digits.startswith("00"):
        digits = digits[2:]

    # Egyptian mobile (010, 011, 012, 015 - 11 digits)
    if len(digits) == 11 and digits.startswith(("010", "011", "012", "015")):
        digits = "2" + digits

    # Saudi mobile (05xxxxxxxx - 10 digits)
    elif len(digits) == 10 and digits.startswith("05"):
        digits = "966" + digits[1:]

    return digits


class WhatsAppGatewayClient:
    def __init__(self):
        self.base_url = settings.BAILEYS_GATEWAY_URL.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "X-Internal-Token": settings.BAILEYS_INTERNAL_TOKEN
        }

    async def get_status(self) -> Dict[str, Any]:
        """Checks if Baileys gateway is running and connected to WhatsApp."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(
                    f"{self.base_url}/api/status",
                    headers=self.headers
                )
                if res.status_code == 200:
                    return res.json()
                return {"connected": False, "status": f"Gateway error {res.status_code}"}
        except httpx.RequestError as e:
            return {"connected": False, "status": f"Gateway unreachable: {str(e)}"}

    async def send_message(self, raw_phone: str, message: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Sends WhatsApp message via the Baileys gateway.
        Returns: (success, status_message, response_data)
        """
        phone = normalize_phone_number(raw_phone)
        payload = {
            "phone_number": phone,
            "message": message
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/send-message",
                    headers=self.headers,
                    json=payload
                )

                data = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}

                if res.status_code == 200 and data.get("success"):
                    return True, "تم إرسال الرسالة عبر الواتساب بنجاح.", data
                
                err_msg = data.get("message") or res.text or f"Error HTTP {res.status_code}"
                return False, f"فشل إرسال الرسالة عبر الواتساب: {err_msg}", data

        except httpx.ConnectError:
            return False, "بوابة الواتساب (Baileys Gateway) غير متصلة أو متوقفة عن العمل.", None
        except httpx.TimeoutException:
            return False, "انتهت مهلة الاتصال ببوابة الواتساب.", None
        except Exception as e:
            return False, f"خطأ غير متوقع أثناء الاتصال ببوابة الواتساب: {str(e)}", None


whatsapp_client = WhatsAppGatewayClient()
