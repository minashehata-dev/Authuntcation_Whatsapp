import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_backend_dir = Path(__file__).resolve().parent.parent
_root_dir = _backend_dir.parent
_possible_env_files = [
    str(_backend_dir / ".env"),
    str(_root_dir / ".env"),
    ".env"
]


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "WhatsApp OTP Service"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Security & Encryption Verification Headers
    # HMAC SHA-256 secret key shared with the platform
    SECRET_KEY: str = "super-secret-hmac-key-change-in-production-123456"
    # Alternative/supplementary Static API Key
    API_KEY: str = "platform-api-key-9876543210"
    
    # Header Names
    SIGNATURE_HEADER: str = "X-Signature"
    TIMESTAMP_HEADER: str = "X-Timestamp"
    API_KEY_HEADER: str = "X-API-Key"
    
    # Maximum allowed drift for timestamp (in seconds) to prevent replay attacks
    MAX_TIMESTAMP_DRIFT_SECONDS: int = 300  # 5 minutes
    
    # Security enforcement mode: "hmac", "apikey", "none", or "both"
    SECURITY_MODE: str = "hmac"  # options: hmac, apikey, none, both

    # OTP Configuration
    OTP_LENGTH: int = 6
    OTP_EXPIRY_SECONDS: int = 300  # 5 minutes
    OTP_RESEND_COOLDOWN_SECONDS: int = 60  # Cooldown between resends to same number
    OTP_MAX_VERIFY_ATTEMPTS: int = 5  # Max wrong attempts before invalidating OTP

    # WhatsApp Baileys Gateway settings
    BAILEYS_GATEWAY_URL: str = "http://127.0.0.1:3001"
    BAILEYS_INTERNAL_TOKEN: str = "internal-baileys-secret-token-abcdef"

    # Branding & Messaging
    BRAND_NAME: str = "Codex Academy"

    model_config = SettingsConfigDict(
        env_file=_possible_env_files,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
