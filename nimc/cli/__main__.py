"""This is just test code. It will be removed in the future."""

from .settings import settings
from core.server import Server

if __name__ == "__main__":
    print(">>>", settings.model_dump())
    print(">>>", settings.hcloud_token)

    # Dump example of firewall rules.
    # firewall = get_firewall(settings.hcloud_token.get_secret_value(), "nimc-firewall")
    # rules = firewall.get("rules", [])
    # print(">>>", json.dumps(rules, indent=2))

    hasturian_server = Server(
        path=settings.servers_dir / "hasturian",
        skeleton_dir=settings.skeleton_dir,
    )
    cloud_config = hasturian_server.render_cloud_config(
        volume_id="12345678",
        hcloud_token=settings.hcloud_token.get_secret_value(),
    )

    # Dump hasturian_server
    print("\nServer config:")
    print(">>>", hasturian_server.config.model_dump())
    print("\nCloud config:")
    print(">>>", cloud_config)
