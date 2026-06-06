from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str
    APP_ENV: str = "development"
    PUBLIC_APP_URL: str = "http://localhost:3000"
    API_PUBLIC_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str = "http://localhost:3000"

    DEV_AUTH_BYPASS: bool = False
    DEV_USER_EMAIL: str = "dev@survey.local"
    DEV_USER_EXTERNAL_ID: str = "dev-user"

    CSRF_SECRET: str = "change-me-csrf-secret"
    APP_SECRET: str = ""

    # auth.vk.team OIDC
    VK_AUTH_ISSUER: str = "https://auth.vk.team"
    VK_AUTH_REALM: str = ""
    VK_AUTH_DISCOVERY_URL: str = ""
    VK_AUTH_CLIENT_ID: str = ""
    VK_AUTH_CLIENT_SECRET: str = ""
    VK_AUTH_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    VK_AUTH_FRONTEND_URL: str = "http://localhost:3000"
    VK_AUTH_SCOPES: str = "openid profile email"
    VK_AUTH_AUDIENCE: str = ""
    VK_AUTH_JWKS_URL: str = ""

    # HashiCorp Vault
    VAULT_ADDR: str = ""
    VAULT_TOKEN: str = ""
    VAULT_MOUNT_POINT: str = "secret"
    VAULT_EXTERNAL_KEYS_PATH: str = "survey-platform/external-api"

    DRAFT_TTL_SECONDS: int = 60 * 60 * 24 * 14
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def vk_discovery_url(self) -> str:
        if self.VK_AUTH_DISCOVERY_URL:
            return self.VK_AUTH_DISCOVERY_URL
        issuer = self.VK_AUTH_ISSUER.rstrip("/")
        if self.VK_AUTH_REALM:
            return f"{issuer}/realms/{self.VK_AUTH_REALM}/.well-known/openid-configuration"
        return f"{issuer}/.well-known/openid-configuration"

    @property
    def vk_audience(self) -> str:
        return self.VK_AUTH_AUDIENCE or self.VK_AUTH_CLIENT_ID

    @property
    def vk_oauth_configured(self) -> bool:
        return bool(self.VK_AUTH_CLIENT_ID and self.VK_AUTH_CLIENT_SECRET)

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in {"production", "prod"}


settings = Settings()
