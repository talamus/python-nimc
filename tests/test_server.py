import textwrap

import jinja2
import pytest
from pydantic import ValidationError

from nimc.core.server import Server, ServerConfig, _load_files, _yaml_block_scalar

MINIMAL_TOML = """\
server_title = "Test Server"
server_slug = "test"
server_version = "1.0.0"
admin_ssh_public_key = "ssh-ed25519 AAAA..."
"""


# -- ServerConfig --


class TestServerConfig:
    def test_minimal_config(self):
        config = ServerConfig(
            server_title="Test",
            server_slug="test",
            server_version="1.0",
            admin_ssh_public_key="ssh-ed25519 AAAA...",
        )
        assert config.server_title == "Test"
        assert config.service_username == "nimc"
        assert config.admin_username == "admin"
        assert config.maintenance_mode is False
        assert config.apt_packages == []
        assert config.ports == []

    def test_defaults_from_slug(self):
        config = ServerConfig(
            server_title="Test",
            server_slug="minecraft",
            server_version="1.0",
            admin_ssh_public_key="ssh-ed25519 AAAA...",
        )
        assert config.server_name == "minecraft-server"
        assert config.primary_ip_name == "minecraft-ip"
        assert config.firewall_name == "minecraft-firewall"
        assert config.volume_name == "minecraft-volume"

    def test_explicit_overrides_slug_defaults(self):
        config = ServerConfig(
            server_title="Test",
            server_slug="minecraft",
            server_version="1.0",
            admin_ssh_public_key="ssh-ed25519 AAAA...",
            server_name="custom-name",
            volume_name="custom-vol",
        )
        assert config.server_name == "custom-name"
        assert config.volume_name == "custom-vol"
        # Others still derived from slug
        assert config.primary_ip_name == "minecraft-ip"

    def test_port_validation(self):
        with pytest.raises(ValidationError):
            ServerConfig(
                server_title="T",
                server_slug="t",
                server_version="1",
                admin_ssh_public_key="k",
                ports=[{"description": "bad", "protocol": "tcp", "port": 0}],
            )

    def test_port_protocol_literal(self):
        with pytest.raises(ValidationError):
            ServerConfig(
                server_title="T",
                server_slug="t",
                server_version="1",
                admin_ssh_public_key="k",
                ports=[{"description": "bad", "protocol": "icmp", "port": 80}],
            )


# -- _yaml_block_scalar --


class TestYamlBlockScalar:
    def test_simple(self):
        result = _yaml_block_scalar("line1\nline2\n")
        assert result == "|\n      line1\n      line2"

    def test_empty_lines_preserved(self):
        result = _yaml_block_scalar("a\n\nb\n")
        assert result == "|\n      a\n\n      b"

    def test_custom_indent(self):
        result = _yaml_block_scalar("hello\n", indent=2)
        assert result == "|\n  hello"

    def test_trailing_newlines_stripped(self):
        result = _yaml_block_scalar("x\n\n\n")
        assert result == "|\n      x"


# -- _load_files --


class TestLoadFiles:
    def test_single_directory(self, tmp_path):
        d = tmp_path / "files"
        d.mkdir()
        (d / "a.txt").write_text("aaa")
        (d / "b.txt").write_text("bbb")

        result = _load_files(d)
        assert result == {"a.txt": "aaa", "b.txt": "bbb"}

    def test_override(self, tmp_path):
        skeleton = tmp_path / "skeleton"
        skeleton.mkdir()
        (skeleton / "shared.txt").write_text("skeleton version")
        (skeleton / "only_skeleton.txt").write_text("only in skeleton")

        override = tmp_path / "override"
        override.mkdir()
        (override / "shared.txt").write_text("override version")
        (override / "only_override.txt").write_text("only in override")

        result = _load_files(skeleton, override)
        assert result["shared.txt"] == "override version"
        assert result["only_skeleton.txt"] == "only in skeleton"
        assert result["only_override.txt"] == "only in override"

    def test_missing_directory_skipped(self, tmp_path):
        existing = tmp_path / "exists"
        existing.mkdir()
        (existing / "a.txt").write_text("a")

        missing = tmp_path / "nope"
        result = _load_files(existing, missing)
        assert result == {"a.txt": "a"}

    def test_no_directories(self, tmp_path):
        result = _load_files(tmp_path / "nope")
        assert result == {}


# -- Server --


class TestServer:
    @pytest.fixture()
    def skeleton_dir(self, tmp_path):
        """Create a minimal skeleton directory."""
        skeleton = tmp_path / "server_skeleton"
        skeleton.mkdir()
        (skeleton / "files").mkdir()
        (skeleton / "files" / "greeting.j2").write_text("Hello {{ admin_username }}!\n")
        (skeleton / "cloud-config.yaml.j2").write_text(
            textwrap.dedent("""\
                #cloud-config
                admin: {{ admin_username }}
                write_files:
                  - path: /etc/greeting
                    content: {{ files_greeting }}
            """)
        )
        return skeleton

    @pytest.fixture()
    def server_dir(self, tmp_path):
        """Create a minimal server config directory."""
        srv = tmp_path / "servers" / "myserver"
        srv.mkdir(parents=True)
        (srv / "server.toml").write_text(MINIMAL_TOML)
        return srv

    def test_loads_config(self, server_dir, skeleton_dir):
        server = Server(server_dir, skeleton_dir)
        assert server.config.server_slug == "test"
        assert server.config.server_title == "Test Server"

    def test_loads_skeleton_files(self, server_dir, skeleton_dir):
        server = Server(server_dir, skeleton_dir)
        assert "greeting.j2" in server.files

    def test_server_files_override_skeleton(self, server_dir, skeleton_dir):
        files_dir = server_dir / "files"
        files_dir.mkdir()
        (files_dir / "greeting.j2").write_text("Custom hello {{ admin_username }}!\n")

        server = Server(server_dir, skeleton_dir)
        assert "Custom" in server.files["greeting.j2"]

    def test_render_cloud_config(self, server_dir, skeleton_dir):
        server = Server(server_dir, skeleton_dir)
        result = server.render_cloud_config()

        assert "#cloud-config" in result
        assert "admin: admin" in result
        assert "Hello admin!" in result

    def test_render_with_extra_vars(self, server_dir, skeleton_dir):
        (skeleton_dir / "files" / "greeting.j2").write_text(
            "Hello {{ admin_username }}, token={{ token }}!\n"
        )

        server = Server(server_dir, skeleton_dir)
        result = server.render_cloud_config(token="secret123")
        assert "token=secret123" in result

    def test_render_missing_var_raises(self, server_dir, skeleton_dir):
        (skeleton_dir / "files" / "greeting.j2").write_text("{{ undefined_var }}\n")

        server = Server(server_dir, skeleton_dir)
        with pytest.raises(jinja2.UndefinedError):
            server.render_cloud_config()

    def test_render_files_as_yaml_block_scalar(self, server_dir, skeleton_dir):
        server = Server(server_dir, skeleton_dir)
        result = server.render_cloud_config()

        # The file content should be a YAML block scalar (starts with |)
        assert "content: |\n" in result
        assert "      Hello admin!" in result
