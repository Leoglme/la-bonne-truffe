"""
Configuration settings for the La Bonne Truffe API, read from the environment (``.env``).
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from enums.listing_source import ListingSource


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, populate_by_name=True, extra="ignore"
    )

    env: str = "development"
    debug: bool = True
    api_version: str = "v1"
    api_prefix: str = "/api/v1"
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    web_base_url: str = Field(
        default="http://localhost:3000",
        alias="WEB_BASE_URL",
        description="Public URL of the dashboard, used to build the links opened from a notification",
    )

    host: str = "0.0.0.0"
    port: int = 8000

    cors_origins_str: str | None = Field(
        default="http://localhost:3000,tauri://localhost,http://tauri.localhost",
        alias="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins",
    )

    database_url: str = Field(default="sqlite:///./data/la-bonne-truffe.db", alias="DATABASE_URL")

    secret_key: str = Field(default="dev-secret-key-change-in-production", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=43200,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="Access token lifetime in minutes: a single user and no refresh token, so sessions are long",
    )

    admin_name: str = Field(default="Léo", alias="ADMIN_NAME")
    admin_email: str = Field(default="contact@dibodev.fr", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="change-me", alias="ADMIN_PASSWORD")

    signup_enabled: bool = Field(
        default=False,
        alias="SIGNUP_ENABLED",
        description="Whether the signup screen creates accounts; closed, it keeps each attempt and tells the admin",
    )
    password_reset_token_expire_minutes: int = Field(
        default=30,
        alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
        description="Lifetime of the link sent by « Mot de passe oublié »",
    )

    resend_api_key: str = Field(
        default="",
        alias="RESEND_API_KEY",
        description="Resend API key; when empty (development), the emails are written to the log instead",
    )
    email_from: str = Field(
        default="La Bonne Truffe <contact@dibodev.fr>",
        alias="EMAIL_FROM",
        description="Sender of the account emails, on a domain verified in Resend",
    )

    vapid_public_key: str | None = Field(default=None, alias="VAPID_PUBLIC_KEY")
    vapid_private_key_b64: str | None = Field(
        default=None,
        alias="VAPID_PRIVATE_KEY_B64",
        description="Base64 of the PKCS8 PEM VAPID private key",
    )
    vapid_subject: str = Field(default="mailto:contact@dibodev.fr", alias="VAPID_SUBJECT")

    collect_user_agent_contact: str = Field(
        default="contact@dibodev.fr",
        alias="COLLECT_USER_AGENT_CONTACT",
        description="Email written in the honest User-Agent sent to the HTML sources",
    )
    collect_skipped_sources_str: str | None = Field(
        default=None,
        alias="COLLECT_SKIPPED_SOURCES",
        description="Comma-separated sources this machine does not collect",
    )

    @property
    def allowed_cors_origins(self) -> list[str]:
        """The CORS origins as a list, blanks dropped."""
        if not self.cors_origins_str:
            return []
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

    @property
    def honest_user_agent(self) -> str:
        """The User-Agent sent to the sources that accept a bot naming itself."""
        return f"LaBonneTruffe/1.0 (+mailto:{self.collect_user_agent_contact})"

    @property
    def collect_skipped_sources(self) -> frozenset[ListingSource]:
        """
        The sources this machine does not collect, blanks dropped.

        Raises:
            ValueError: For a name that is not a source.
        """
        if not self.collect_skipped_sources_str:
            return frozenset()
        return frozenset(
            ListingSource(source_name.strip())
            for source_name in self.collect_skipped_sources_str.split(",")
            if source_name.strip()
        )


settings = Settings()
