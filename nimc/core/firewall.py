from hcloud import Client
from hcloud.firewalls.domain import Firewall, FirewallRule

from core.exceptions import MissingResource
from core.server import FixedSource, ServerConfig


def build_rules_for_source(
    config: ServerConfig,
    name: str,
    ip: str,
    is_admin: bool,
) -> list[dict]:
    """Build hcloud firewall rules for a single source IP.

    :param config: Server configuration with port definitions.
    :param name: Identifier for rule descriptions, e.g. "tero", "master".
    :param ip: IPv4 address of the source.
    :param is_admin: Whether this source gets admin-level access.
    :return: List of rule dicts ready for set_firewall_rules().
    """
    source_cidr = f"{ip}/32"
    rules: list[dict] = []

    ports = config.admin_ports if is_admin else config.service_ports

    for port in ports:
        rules.append(
            {
                "direction": "in",
                "protocol": port.protocol,
                "port": str(port.port),
                "source_ips": [source_cidr],
                "destination_ips": [],
                "description": f"{port.description} [{name}]",
            }
        )

    if is_admin:
        rules.append(
            {
                "direction": "in",
                "protocol": "tcp",
                "port": "22",
                "source_ips": [source_cidr],
                "destination_ips": [],
                "description": f"SSH [{name}]",
            }
        )
        rules.append(
            {
                "direction": "in",
                "protocol": "icmp",
                "port": None,
                "source_ips": [source_cidr],
                "destination_ips": [],
                "description": f"ICMP [{name}]",
            }
        )

    return rules


def update_firewall_access(
    token: str,
    config: ServerConfig,
    name: str,
    ip: str,
    is_admin: bool,
) -> dict:
    """Update firewall rules for a single source (user or fixed source).

    Downloads current rules, removes all rules tagged with [name],
    adds new rules for the given IP, and pushes the result.

    :param token: Hetzner Cloud API token.
    :param config: Server configuration.
    :param name: Source identifier (username or fixed source name).
    :param ip: IPv4 address.
    :param is_admin: Whether this source gets admin-level access.
    :return: Dict with updated firewall information.
    """
    firewall = get_firewall(token, config.firewall_name)
    existing_rules = firewall["rules"]

    tag = f"[{name}]"
    filtered = [r for r in existing_rules if tag not in (r.get("description") or "")]

    new_rules = build_rules_for_source(config, name, ip, is_admin)

    return set_firewall_rules(token, config.firewall_name, filtered + new_rules)


def sync_fixed_sources(
    token: str,
    config: ServerConfig,
    fixed_sources: list[FixedSource],
) -> dict:
    """Ensure all fixed sources have full access on this server's firewall.

    Fixed sources always get admin-level access (all ports + SSH + ICMP).

    :param token: Hetzner Cloud API token.
    :param config: Server configuration.
    :param fixed_sources: List of fixed sources to sync.
    :return: Dict with updated firewall information.
    """
    firewall = get_firewall(token, config.firewall_name)
    existing_rules = firewall["rules"]

    fixed_names = {fs.name for fs in fixed_sources}
    filtered = [
        r
        for r in existing_rules
        if not any(f"[{name}]" in (r.get("description") or "") for name in fixed_names)
    ]

    new_rules: list[dict] = []
    for fs in fixed_sources:
        new_rules.extend(build_rules_for_source(config, fs.name, fs.ip, is_admin=True))

    return set_firewall_rules(token, config.firewall_name, filtered + new_rules)


def get_firewall(token: str, firewall_id_or_name: int | str) -> dict:
    """Fetch a firewall by ID or name from Hetzner Cloud.

    :param token: Hetzner Cloud API token.
    :param firewall_id_or_name: Firewall ID (int) or name (str).
    :return: Dict with firewall id, name, labels, rules, applied_to, and created.
    :raises MissingResource: If the firewall is not found.
    """
    client = Client(token)
    firewall = _get_firewall_by_id_or_name(client, firewall_id_or_name)
    return _serialize_firewall(firewall.data_model)


def set_firewall_rules(
    token: str, firewall_id_or_name: int | str, rules: list[dict]
) -> dict:
    """Set firewall rules for a given firewall.

    :param token: Hetzner Cloud API token.
    :param firewall_id_or_name: Firewall ID (int) or name (str).
    :param rules: List of rule dicts to set on the firewall.
    :return: Dict with updated firewall information.
    :raises MissingResource: If the firewall is not found.
    """
    client = Client(token)
    firewall = _get_firewall_by_id_or_name(client, firewall_id_or_name)

    # Convert dict rules to FirewallRule objects
    rule_objects = [FirewallRule(**rule) for rule in rules]

    # Update the firewall with new rules
    updated_firewall = client.firewalls.update(id=firewall.id, rules=rule_objects)

    return _serialize_firewall(updated_firewall.data_model)


def _get_firewall_by_id_or_name(
    client: Client, firewall_id_or_name: int | str
) -> Firewall | None:
    """Helper function to fetch a firewall by ID or name."""
    firewall = None
    if isinstance(firewall_id_or_name, int):
        firewall = client.firewalls.get_by_id(firewall_id_or_name)
    else:
        firewall = client.firewalls.get_by_name(firewall_id_or_name)
    if firewall is None:
        raise MissingResource(
            "firewall",
            firewall_id_or_name,
            help="Ensure the firewall exists and the token has access.",
        )
    return firewall


def _serialize_firewall(fw: Firewall) -> dict:
    """Convert a Firewall domain object to a plain dict."""
    return {
        "id": fw.id,
        "name": fw.name,
        "labels": fw.labels or {},
        "created": fw.created.isoformat() if fw.created else None,
        "rules": [_serialize_rule(r) for r in (fw.rules or [])],
        "applied_to": [_serialize_resource(r) for r in (fw.applied_to or [])],
    }


def _serialize_rule(rule) -> dict:
    """Convert a FirewallRule to a plain dict."""
    return {
        "direction": rule.direction,
        "protocol": rule.protocol,
        "port": rule.port,
        "source_ips": rule.source_ips,
        "destination_ips": rule.destination_ips,
        "description": rule.description,
    }


def _serialize_resource(resource) -> dict:
    """Convert a FirewallResource to a plain dict."""
    result: dict = {"type": resource.type}
    if resource.server is not None:
        result["server"] = {"id": resource.server.id}
    if resource.label_selector is not None:
        result["label_selector"] = resource.label_selector.selector
    return result
