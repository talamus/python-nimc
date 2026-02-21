from nimc.core.firewall import build_rules_for_source
from nimc.core.server import ServerConfig


def _make_config(**overrides) -> ServerConfig:
    """Create a minimal ServerConfig for testing."""
    defaults = {
        "server_title": "Test",
        "server_slug": "test",
        "server_version": "1.0",
        "admin_ssh_public_key": "ssh-ed25519 AAAA...",
        "ports": [
            {"description": "Game TCP", "protocol": "tcp", "port": 25565},
            {"description": "Game UDP", "protocol": "udp", "port": 25565},
        ],
    }
    defaults.update(overrides)
    return ServerConfig(**defaults)


class TestBuildRulesForSource:
    def test_regular_user_gets_service_ports_only(self):
        config = _make_config()
        rules = build_rules_for_source(config, "anne", "1.2.3.4", is_admin=False)

        assert len(rules) == 2
        descriptions = {r["description"] for r in rules}
        assert descriptions == {"Game TCP [anne]", "Game UDP [anne]"}

        for r in rules:
            assert r["direction"] == "in"
            assert r["source_ips"] == ["1.2.3.4/32"]

    def test_admin_user_gets_all_ports_plus_ssh_and_icmp(self):
        config = _make_config()
        rules = build_rules_for_source(config, "tero", "5.6.7.8", is_admin=True)

        descriptions = {r["description"] for r in rules}
        assert "Game TCP [tero]" in descriptions
        assert "Game UDP [tero]" in descriptions
        assert "SSH [tero]" in descriptions
        assert "ICMP [tero]" in descriptions
        assert len(rules) == 4

    def test_admin_only_port_excluded_for_regular_user(self):
        config = _make_config(
            ports=[
                {"description": "Game TCP", "protocol": "tcp", "port": 25565},
                {
                    "description": "Web Panel",
                    "protocol": "tcp",
                    "port": 8080,
                    "admin_only": True,
                },
            ]
        )
        rules = build_rules_for_source(config, "anne", "1.2.3.4", is_admin=False)

        descriptions = {r["description"] for r in rules}
        assert "Game TCP [anne]" in descriptions
        assert "Web Panel [anne]" not in descriptions
        assert len(rules) == 1

    def test_admin_gets_admin_only_ports(self):
        config = _make_config(
            ports=[
                {"description": "Game TCP", "protocol": "tcp", "port": 25565},
                {
                    "description": "Web Panel",
                    "protocol": "tcp",
                    "port": 8080,
                    "admin_only": True,
                },
            ]
        )
        rules = build_rules_for_source(config, "tero", "5.6.7.8", is_admin=True)

        descriptions = {r["description"] for r in rules}
        assert "Game TCP [tero]" in descriptions
        assert "Web Panel [tero]" in descriptions
        assert "SSH [tero]" in descriptions
        assert "ICMP [tero]" in descriptions

    def test_icmp_rule_has_no_port(self):
        config = _make_config()
        rules = build_rules_for_source(config, "tero", "5.6.7.8", is_admin=True)

        icmp_rules = [r for r in rules if r["protocol"] == "icmp"]
        assert len(icmp_rules) == 1
        assert icmp_rules[0]["port"] is None

    def test_ssh_rule_is_port_22_tcp(self):
        config = _make_config()
        rules = build_rules_for_source(config, "tero", "5.6.7.8", is_admin=True)

        ssh_rules = [r for r in rules if r["description"] == "SSH [tero]"]
        assert len(ssh_rules) == 1
        assert ssh_rules[0]["protocol"] == "tcp"
        assert ssh_rules[0]["port"] == "22"

    def test_port_is_string_in_rules(self):
        config = _make_config()
        rules = build_rules_for_source(config, "anne", "1.2.3.4", is_admin=False)

        for r in rules:
            if r["port"] is not None:
                assert isinstance(r["port"], str)

    def test_source_ip_has_cidr_suffix(self):
        config = _make_config()
        rules = build_rules_for_source(config, "anne", "10.0.0.1", is_admin=False)

        for r in rules:
            assert r["source_ips"] == ["10.0.0.1/32"]

    def test_empty_ports_regular_user_gets_no_rules(self):
        config = _make_config(ports=[])
        rules = build_rules_for_source(config, "anne", "1.2.3.4", is_admin=False)
        assert rules == []

    def test_empty_ports_admin_still_gets_ssh_and_icmp(self):
        config = _make_config(ports=[])
        rules = build_rules_for_source(config, "tero", "5.6.7.8", is_admin=True)

        descriptions = {r["description"] for r in rules}
        assert descriptions == {"SSH [tero]", "ICMP [tero]"}


class TestServerConfigPortProperties:
    def test_service_ports_excludes_admin_only(self):
        config = _make_config(
            ports=[
                {"description": "Game", "protocol": "tcp", "port": 25565},
                {
                    "description": "Panel",
                    "protocol": "tcp",
                    "port": 8080,
                    "admin_only": True,
                },
            ]
        )
        assert len(config.service_ports) == 1
        assert config.service_ports[0].description == "Game"

    def test_admin_ports_includes_all(self):
        config = _make_config(
            ports=[
                {"description": "Game", "protocol": "tcp", "port": 25565},
                {
                    "description": "Panel",
                    "protocol": "tcp",
                    "port": 8080,
                    "admin_only": True,
                },
            ]
        )
        assert len(config.admin_ports) == 2
