"""Original guide helper. No installation, Docker mutation, or network requests.

--init exclusively creates one private .env after validating the photo mount.
Without --init, only checks local settings and storage. Never prints passwords.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

VERSION = "v3.3.6"
UUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z")
UPSTREAM_SHA = "2601c893aa3217d3c0c7284c23aaa1699aac75b533c84c0315fd16b7889fd552"


def read_env(path):
    data = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("Invalid .env line; values were not displayed")
        name, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z_]+", name) or name in data:
            raise ValueError("Invalid or duplicate .env key")
        data[name] = value
    return data


def validate_env(data):
    expected = {
        "IMMICH_VERSION": VERSION,
        "UPLOAD_LOCATION": "/mnt/photos/immich",
        "DB_DATA_LOCATION": "/srv/immich-db/postgres",
        "TZ": "Asia/Tokyo",
        "DB_USERNAME": "postgres",
        "DB_DATABASE_NAME": "immich",
    }
    for name, value in expected.items():
        if data.get(name) != value:
            raise ValueError("Unexpected guide setting: " + name)
    if not re.fullmatch(r"[0-9a-f]{48}", data.get("DB_PASSWORD", "")):
        raise ValueError("DB_PASSWORD must be generated locally by --init")
    if not UUID.fullmatch(data.get("PHOTO_DISK_UUID", "")):
        raise ValueError("PHOTO_DISK_UUID is missing or invalid")
    return data


def check_mount(expected_uuid, runner=subprocess.run):
    if not UUID.fullmatch(expected_uuid):
        raise ValueError("Invalid photo disk UUID")
    result = runner(
        ["findmnt", "--noheadings", "--mountpoint", "/mnt/photos", "--output", "UUID,FSTYPE"],
        capture_output=True, text=True, check=False,
    )
    fields = result.stdout.strip().split()
    if result.returncode or len(fields) != 2 or fields[0].lower() != expected_uuid.lower() or fields[1] != "ext4":
        raise ValueError("Photo SSD is absent, has a different UUID, or is not ext4; stopped")


def make_env(uuid):
    if not UUID.fullmatch(uuid):
        raise ValueError("Invalid photo disk UUID")
    return "\n".join([
        "IMMICH_VERSION=" + VERSION,
        "UPLOAD_LOCATION=/mnt/photos/immich",
        "DB_DATA_LOCATION=/srv/immich-db/postgres",
        "TZ=Asia/Tokyo",
        "DB_PASSWORD=" + secrets.token_hex(24),
        "DB_USERNAME=postgres", "DB_DATABASE_NAME=immich",
        "PHOTO_DISK_UUID=" + uuid, "",
    ])


def create_env(path, uuid):
    content = make_env(uuid)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
        file.write(content)


def check_files(root):
    upstream = root / "docker-compose.yml"
    if hashlib.sha256(upstream.read_bytes()).hexdigest() != UPSTREAM_SHA:
        raise ValueError("Official Compose hash mismatch; do not start")
    for name in ("docker-compose.override.yml", "immich-config.json"):
        if not (root / name).is_file() or (root / name).is_symlink():
            raise ValueError("Missing or linked guide file: " + name)
    config = json.loads((root / "immich-config.json").read_text(encoding="utf-8-sig"))
    if config.get("machineLearning", {}).get("enabled") is not False:
        raise ValueError("Beginner guide requires machine learning disabled")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--ssd-uuid")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    env = root / ".env"
    if env.is_symlink():
        raise ValueError("Linked .env rejected")
    check_files(root)
    if args.init:
        if not args.ssd_uuid:
            raise ValueError("--ssd-uuid is required with --init")
        check_mount(args.ssd_uuid)
        create_env(env, args.ssd_uuid)
        print("Private .env created without overwrite. Password was not displayed.")
    settings = validate_env(read_env(env))
    check_mount(settings["PHOTO_DISK_UUID"])
    for name in ("UPLOAD_LOCATION", "DB_DATA_LOCATION"):
        path = Path(settings[name])
        if not path.is_dir() or path.resolve() != path:
            raise ValueError("Missing or linked storage path: " + name)
    if os.name == "posix" and env.stat().st_mode & 0o077:
        raise ValueError(".env must not be accessible to group/others; set chmod 600 .env")
    print("PASS: pinned release, local settings and photo SSD mount checked. Docker has not been started.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print("STOP: " + str(error), file=sys.stderr)
        sys.exit(1)
