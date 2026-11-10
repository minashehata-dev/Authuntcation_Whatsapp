import sys
import os
import time

# Ensure backend and app directory are always in sys.path regardless of where main.py is executed
_app_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_app_dir)
for _p in [_backend_dir, _app_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.config import settings
    from app.models import (
        SendOtpRequest,
        SendOtpResponse,
        VerifyOtpRequest,
        VerifyOtpResponse,
        WhatsAppStatusResponse
    )
    from app.security import verify_security_header, compute_signature
    from app.otp_service import otp_service
    from app.message_builder import build_whatsapp_otp_message
    from app.whatsapp_client import whatsapp_client, normalize_phone_number
except ImportError:
    from config import settings
    from models import (
        SendOtpRequest,
        SendOtpResponse,
        VerifyOtpRequest,
        VerifyOtpResponse,
        WhatsAppStatusResponse
    )
    from security import verify_security_header, compute_signature
    from otp_service import otp_service
    from message_builder import build_whatsapp_otp_message
    from whatsapp_client import whatsapp_client, normalize_phone_number


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for OTP verification and WhatsApp delivery via Baileys",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
async def root():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "security_mode": settings.SECURITY_MODE,
        "docs": "/docs"
    }


@app.get("/health", tags=["General"])
async def health_check():
    gateway_status = await whatsapp_client.get_status()
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "whatsapp_gateway": gateway_status
    }


@app.get("/api/v1/whatsapp/status", response_model=WhatsAppStatusResponse, tags=["WhatsApp Gateway"])
async def get_whatsapp_status():
    """Checks WhatsApp connection status via the Baileys gateway."""
    status_data = await whatsapp_client.get_status()
    is_connected = status_data.get("connected", False)
    return WhatsAppStatusResponse(
        connected=is_connected,
        status="متصل بالواتساب ومستعد للإرسال" if is_connected else "غير متصل بالواتساب (يرجى مسح رمز QR)",
        details=status_data
    )


@app.post(
    "/api/v1/otp/send",
    response_model=SendOtpResponse,
    dependencies=[Depends(verify_security_header)],
    tags=["OTP Authentication"]
)
async def send_otp(request: SendOtpRequest):
    """
    Receives phone number from the platform, verifies cryptographic signature header,
    generates OTP, formats a beautiful WhatsApp message, and sends it via Baileys.
    """
    normalized_phone = normalize_phone_number(request.phone_number)

    # 1. Create OTP
    success, msg, otp_code, request_id = otp_service.create_otp(normalized_phone)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=msg
        )

    # 2. Build beautiful WhatsApp message
    message_text = build_whatsapp_otp_message(
        code=otp_code,
        user_name=request.user_name,
        purpose=request.purpose,
        locale=request.locale
    )

    # 3. Send message through Baileys WhatsApp Gateway
    sent, send_status_msg, gateway_res = await whatsapp_client.send_message(
        raw_phone=normalized_phone,
        message=message_text
    )

    if not sent:
        # If sending failed, invalidate the OTP so the user is not locked by cooldown
        active_record = otp_service.get_active_otp(normalized_phone)
        if active_record:
            active_record["last_sent_at"] = 0

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "WhatsApp delivery failed",
                "reason": send_status_msg,
                "gateway_response": gateway_res
            }
        )

    return SendOtpResponse(
        success=True,
        message="تم إنشاء كود التحقق وإرساله إلى الواتساب بنجاح.",
        phone_number=normalized_phone,
        expires_in_seconds=settings.OTP_EXPIRY_SECONDS,
        request_id=request_id
    )


@app.post(
    "/api/v1/otp/verify",
    response_model=VerifyOtpResponse,
    dependencies=[Depends(verify_security_header)],
    tags=["OTP Authentication"]
)
async def verify_otp(request: VerifyOtpRequest):
    """
    Verifies the OTP entered by the user against the stored code for that phone number.
    Also protected by the security header.
    """
    normalized_phone = normalize_phone_number(request.phone_number)
    verified, msg = otp_service.verify_otp(
        phone_number=normalized_phone,
        entered_code=request.otp_code
    )

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    return VerifyOtpResponse(
        success=True,
        verified=True,
        message=msg,
        phone_number=normalized_phone
    )


# Helper endpoint for developers/testing (only in DEBUG mode)
if settings.DEBUG:
    @app.post("/api/v1/tools/generate-signature", tags=["Development Tools"])
    async def debug_generate_signature(request: Request):
        """
        Helper tool for development to compute valid HMAC-SHA256 signature
        for testing requests.
        """
        body = await request.body()
        now = str(int(time.time()))
        sig = compute_signature(
            secret_key=settings.SECRET_KEY,
            timestamp=now,
            body=body
        )
        return {
            "timestamp": now,
            "signature": sig,
            "headers": {
                settings.SIGNATURE_HEADER: sig,
                settings.TIMESTAMP_HEADER: now
            }
        }


if __name__ == "__main__":
    import uvicorn
    run_port = settings.PORT
    for idx, arg in enumerate(sys.argv):
        if arg == "--port" and idx + 1 < len(sys.argv):
            try:
                run_port = int(sys.argv[idx + 1])
            except ValueError:
                pass
    print(f"🚀 Starting {settings.APP_NAME} on http://{settings.HOST}:{run_port}")
    try:
        uvicorn.run("app.main:app", host=settings.HOST, port=run_port, reload=True, app_dir=_backend_dir)
    except Exception:
        uvicorn.run(app, host=settings.HOST, port=run_port)
