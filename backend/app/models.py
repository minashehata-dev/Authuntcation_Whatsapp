from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator
import re


def clean_phone_number(v: str) -> str:
    """Removes spaces, plus, dashes, and validates digits."""
    cleaned = re.sub(r"[^\d]", "", v)
    if not cleaned or len(cleaned) < 8 or len(cleaned) > 15:
        raise ValueError("Invalid phone number format. Must contain 8 to 15 digits.")
    return cleaned


class SendOtpRequest(BaseModel):
    phone_number: str = Field(
        ...,
        description="Recipient phone number with or without international country code (e.g. '01012345678' or '+201012345678')",
        examples=["+201012345678", "201012345678", "01012345678"]
    )
    user_name: Optional[str] = Field(
        default=None,
        description="Name of the user for greeting in the message"
    )
    purpose: Optional[str] = Field(
        default="تسجيل الدخول",
        description="Purpose of verification (e.g. تسجيل الدخول, تأكيد الحساب, استعادة كلمة المرور)"
    )
    locale: str = Field(
        default="ar",
        description="Language of message: 'ar' for Arabic, 'en' for English"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional custom metadata associated with the request"
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return clean_phone_number(v)


class SendOtpResponse(BaseModel):
    success: bool
    message: str
    phone_number: str
    expires_in_seconds: int
    request_id: str


class VerifyOtpRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number that received the OTP")
    otp_code: str = Field(..., description="The OTP code entered by the user")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return clean_phone_number(v)

    @field_validator("otp_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        code = v.strip()
        if not code.isdigit():
            raise ValueError("OTP code must contain digits only.")
        return code


class VerifyOtpResponse(BaseModel):
    success: bool
    verified: bool
    message: str
    phone_number: str


class GatewaySendMessageRequest(BaseModel):
    phone_number: str
    message: str


class WhatsAppStatusResponse(BaseModel):
    connected: bool
    status: str
    details: Optional[Dict[str, Any]] = None
