import tomllib
from pathlib import Path
from typing import Literal

import jinja2
from pydantic import BaseModel, Field, model_validator


class Port(BaseModel):
    description: str
    protocol: Literal["tcp", "udp"]
    port: int = Field(ge=1, le=65535)
    admin_only: bool = False


class FixedSource(BaseModel):
    """A fixed IP source that always gets full firewall access."""

    name: str
    ip: str


class ServerConfig(BaseModel):
    server_title: str
    server_slug: str
    server_version: str
    service_username: str = "nimc"
    admin_username: str = "admin"
    admin_ssh_public_key: str
    maintenance_mode: bool = False
    server_name: str | None = None
    primary_ip_name: str | None = None
    firewall_name: str | None = None
    volume_name: str | None = None
    apt_packages: list[str] = []
    ports: list[Port] = []

    @property
    def service_ports(self) -> list[Port]:
        """Ports accessible to regular users."""
        return [p for p in self.ports if not p.admin_only]

    @property
    def admin_ports(self) -> list[Port]:
        """All ports (service + admin-only), for admin users."""
        return list(self.ports)

    @model_validator(mode="after")
    def set_defaults_from_slug(self) -> "ServerConfig":
        slug = self.server_slug
        if self.server_name is None:
            self.server_name = f"{slug}-server"
        if self.primary_ip_name is None:
            self.primary_ip_name = f"{slug}-ip"
        if self.firewall_name is None:
            self.firewall_name = f"{slug}-firewall"
        if self.volume_name is None:
            self.volume_name = f"{slug}-volume"
        return self


def _yaml_block_scalar(text: str, indent: int = 6) -> str:
    """Format text as a YAML literal block scalar."""
    prefix = " " * indent
    lines = text.rstrip("\n").split("\n")
    indented_lines = [prefix + line if line else "" for line in lines]
    return "|\n" + "\n".join(indented_lines)


def _load_files(*dirs: Path) -> dict[str, str]:
    """Load files from directories, later directories override earlier ones."""
    files: dict[str, str] = {}
    for d in dirs:
        if d.is_dir():
            for f in sorted(d.iterdir()):
                if f.is_file():
                    files[f.name] = f.read_text()
    return files


class Server:
    """An nimc server loaded from a directory."""

    def __init__(self, path: Path, skeleton_dir: Path) -> None:
        self.path = path
        self.config = ServerConfig.model_validate(
            tomllib.loads((path / "server.toml").read_text())
        )
        self.cloud_config_template = (skeleton_dir / "cloud-config.yaml.j2").read_text()
        self.files = _load_files(skeleton_dir / "files", path / "files")

    def render_cloud_config(self, **extra_vars: str) -> str:
        """Render the cloud-config with config values, rendered files, and extra vars."""
        env = jinja2.Environment(
            undefined=jinja2.StrictUndefined,
            keep_trailing_newline=True,
        )

        context: dict[str, object] = self.config.model_dump()
        context.update(extra_vars)

        # Render each file template and format as YAML block scalar
        for filename, template_str in self.files.items():
            rendered = env.from_string(template_str).render(context)
            var_name = "files_" + filename.removesuffix(".j2").replace(".", "_")
            context[var_name] = _yaml_block_scalar(rendered)

        return env.from_string(self.cloud_config_template).render(context)
