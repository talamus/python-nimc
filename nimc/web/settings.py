"""Application configuration using pydantic-settings"""

from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field, Secret, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.server import FixedSource

# Project root directory (parent of nimc/)
ROOT_PATH = Path(__file__).parent.parent.parent
ACCESS_TOKEN_EXPIRE_HOURS = 24 + 12


class Settings(BaseSettings):
    """Application configuration using pydantic-settings"""

    # JWT Configuration
    secret_key: Secret[str] = Field(
        default="Don't use this in production!",
        description="Secret key for JWT token signing",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=ACCESS_TOKEN_EXPIRE_HOURS * 60,
        description=f"Token expiration in minutes ({ACCESS_TOKEN_EXPIRE_HOURS} hours)",
    )

    # Security Configuration
    secure_cookies: bool = Field(
        default=False, description="Enable secure flag on cookies (HTTPS only)"
    )
    csrf_secret_key: Optional[Secret[str]] = Field(
        default=None, description="CSRF secret key (defaults to secret_key)"
    )

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(
        default=True, description="Enable auto-reload (in development mode only)"
    )
    serve_static_files: bool = Field(default=True, description="Serve static files")

    # Application Settings
    app_name: str = Field(default="NIMC Web UI", description="Application name")
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="screen", description="Logging format (json, screen, default)"
    )
    servers_dir: Path = Field(
        default=ROOT_PATH / "servers",
        description="Path to server config directories",
    )
    skeleton_dir: Path = Field(
        default=ROOT_PATH / "server_skeleton",
        description="Path to the server skeleton template directory",
    )

    # Hetzner Cloud Configuration
    hcloud_token: Secret[str] = Field(
        default="",
        description="Hetzner Cloud API token",
        validation_alias=AliasChoices("adhoc_hcloud_token", "hcloud_token"),
    )

    # Firewall Configuration
    fixed_sources: list[FixedSource] = Field(
        default=[],
        description="Fixed IP sources with full firewall access (JSON list)",
    )

    # Database Configuration
    database_url: str = Field(
        default=f"sqlite:///{ROOT_PATH / 'nimc_web_users.db'}",
        description="Database URL",
    )

    model_config = SettingsConfigDict(
        env_prefix="ADHOC_",  # Environment variables must start with ADHOC_
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is uppercase"""
        return v.upper()

    @model_validator(mode="after")
    def default_csrf_key(self) -> "Settings":
        """Default CSRF key to secret_key if not provided"""
        if self.csrf_secret_key is None:
            self.csrf_secret_key = Secret(self.secret_key.get_secret_value())
        return self


# Create settings instance
settings = Settings()
