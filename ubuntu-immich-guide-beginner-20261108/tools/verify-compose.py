"""Read `docker compose config --format json` from stdin; do not log secrets."""
import json
import sys


def verify(config):
    services = config.get("services", {})
    for name in ("immich-server", "database", "redis"):
        if name not in services:
            raise ValueError("Required service missing: " + name)
    for name, service in services.items():
        if service.get("privileged") or service.get("network_mode") == "host":
            raise ValueError("Unexpected privileged or host-network service")
        if service.get("restart") != "no":
            raise ValueError("Automatic restart is outside this beginner setup")
        if name != "immich-server" and service.get("ports"):
            raise ValueError("An internal service publishes a port")
    app = services["immich-server"]
    if app.get("image") != "ghcr.io/immich-app/immich-server:v3.3.6":
        raise ValueError("Immich version differs from guide")
    ports = app.get("ports", [])
    if len(ports) != 1:
        raise ValueError("Expected exactly one application port")
    port = ports[0]
    if port.get("host_ip") != "127.0.0.1" or str(port.get("published")) != "2283" or port.get("target") != 2283 or port.get("protocol", "tcp") != "tcp":
        raise ValueError("Immich must bind only loopback TCP 2283")
    for name, target, source in (
        ("immich-server", "/data", "/mnt/photos/immich"),
        ("database", "/var/lib/postgresql/data", "/srv/immich-db/postgres"),
    ):
        volumes = [v for v in services[name].get("volumes", []) if v.get("target") == target]
        if len(volumes) != 1 or volumes[0].get("type") != "bind" or volumes[0].get("source") != source or volumes[0].get("bind", {}).get("create_host_path") is not False:
            raise ValueError("Unexpected storage binding: " + name)
    if app.get("environment", {}).get("IMMICH_CONFIG_FILE") != "/config/immich-config.json":
        raise ValueError("Guide configuration file is not enabled")
    if "immich-machine-learning" in services and "optional-ml" not in services["immich-machine-learning"].get("profiles", []):
        raise ValueError("ML must not be a default-start service")


if __name__ == "__main__":
    try:
        verify(json.load(sys.stdin))
        print("PASS: Compose has the expected loopback port and storage bindings. No credential values displayed.")
    except (ValueError, KeyError, TypeError) as error:
        print("STOP: " + str(error), file=sys.stderr)
        sys.exit(1)
