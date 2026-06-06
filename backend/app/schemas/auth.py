from pydantic import BaseModel

from app.models.enums import UserRole


class AuthConfigResponse(BaseModel):
    oauth_configured: bool
    dev_auth_bypass: bool
    login_url: str
    authorization_url: str
    discovery_url: str
    discovery_error: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
