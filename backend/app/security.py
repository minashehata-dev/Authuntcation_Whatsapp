import sys
import os
import hmac
import hashlib
import time
from typing import Optional
from fastapi import Request, HTTPException, status

_app_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_app_dir)
for _p in [_backend_dir, _app_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from app.config import settings
except ImportError:
    from config import settings


def compute_signature(secret_key: str, timestamp: str, body: bytes) -> str:
    """
    Computes HMAC-SHA256 signature over timestamp and raw body.
    Format: HMAC-SHA256(secret_key, timestamp + "." + raw_body)
    """
    payload = f"{timestamp}.".encode("utf-8") + body
    return hmac.new(
        key=secret_key.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()


async def verify_security_header(request: Request) -> bool:
    """
    Validates cryptographic signature / authentication header sent by the platform.
    
    Headers evaluated:
    - X-Signature: HMAC-SHA256 hex digest
    - X-Timestamp: Unix timestamp (seconds) when request was created
    - X-API-Key: Optional or alternative API Key
    
    Raises HTTPException(401) on failure.
    """
    raw_body = await request.body()
    
    # 1. API-Key Check (if mode is 'apikey' or 'both')
    if settings.SECURITY_MODE in ("apikey", "both"):
        api_key = request.headers.get(settings.API_KEY_HEADER)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Missing required header: {settings.API_KEY_HEADER}"
            )
        if not hmac.compare_digest(api_key, settings.API_KEY):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key"
            )

    # 2. HMAC-SHA256 Cryptographic Signature Check (if mode is 'hmac' or 'both')
    if settings.SECURITY_MODE in ("hmac", "both"):
        signature = request.headers.get(settings.SIGNATURE_HEADER)
        timestamp = request.headers.get(settings.TIMESTAMP_HEADER)

        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Missing signature header: {settings.SIGNATURE_HEADER}"
            )

        if not timestamp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Missing timestamp header: {settings.TIMESTAMP_HEADER}"
            )

        # Verify timestamp to prevent Replay Attacks
        try:
            req_time = int(timestamp)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid timestamp format (must be integer unix timestamp)"
            )

        now = int(time.time())
        if abs(now - req_time) > settings.MAX_TIMESTAMP_DRIFT_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Request expired or timestamp drift too large (possible replay attack)"
            )

        # Compute expected signature
        expected_sig = compute_signature(
            secret_key=settings.SECRET_KEY,
            timestamp=timestamp,
            body=raw_body
        )

        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(expected_sig.lower(), signature.lower()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cryptographic signature verification failed (Tampered or unauthorized request)"
            )

    return True
