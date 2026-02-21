"""CLI configuration using pydantic-settings"""

from pathlib import Path

from pydantic import AliasChoices, Secret, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from nimc.core.server import FixedSource


class Settings(BaseSettings):
    """CLI-specific configuration"""

    # Paths
    servers_dir: Path = Field(
        default=Path("servers"),
        description="Path to server config directories",
    )
    skeleton_dir: Path = Field(
        default=Path("server_skeleton"),
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

    # Output Configuration
    output_format: str = Field(
        default="table", description="Output format (table, json)"
    )

    model_config = SettingsConfigDict(
        env_prefix="ADHOC_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Create settings instance
settings = Settings()
