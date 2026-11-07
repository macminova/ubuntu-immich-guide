"""Offline, mocked checks; not Docker integration or Linux deployment tests."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


p = load('preflight', 'immich-preflight.py')
v = load('compose_check', 'verify-compose.py')
UUID = '00000000-0000-4000-8000-000000000001'


def fixture():
    return {'services': {
        'immich-server': {
            'restart': 'no', 'image': 'ghcr.io/immich-app/immich-server:v3.3.6',
            'ports': [{'host_ip': '127.0.0.1', 'published': '2283', 'target': 2283}],
            'environment': {'IMMICH_CONFIG_FILE': '/config/immich-config.json'},
            'volumes': [{'type': 'bind', 'source': '/mnt/photos/immich', 'target': '/data', 'bind': {'create_host_path': False}}]},
        'database': {'restart': 'no', 'volumes': [{'type': 'bind', 'source': '/srv/immich-db/postgres', 'target': '/var/lib/postgresql/data', 'bind': {'create_host_path': False}}]},
        'redis': {'restart': 'no'}}}


class Helpers(unittest.TestCase):
    def test_environment_generation_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / '.env'
            p.create_env(path, UUID)
            self.assertEqual(p.validate_env(p.read_env(path))['PHOTO_DISK_UUID'], UUID)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / '.env'
            p.create_env(path, UUID)
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                p.create_env(path, UUID)
            self.assertEqual(path.read_bytes(), before)

    def test_passwords_differ(self):
        self.assertNotEqual(p.make_env(UUID), p.make_env(UUID))

    def test_bad_uuid(self):
        with self.assertRaises(ValueError):
            p.make_env('../outside')

    def test_duplicate_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'settings'
            path.write_text('TZ=Asia/Tokyo\nTZ=UTC\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                p.read_env(path)

    def test_mount_pass(self):
        p.check_mount(UUID, lambda *a, **k: types.SimpleNamespace(returncode=0, stdout=UUID + ' ext4'))

    def test_bad_mounts(self):
        for output, code in [('', 1), (UUID + ' ntfs', 0), ('different ext4', 0)]:
            with self.subTest(output=output), self.assertRaises(ValueError):
                p.check_mount(UUID, lambda *a, **k: types.SimpleNamespace(returncode=code, stdout=output))

    def test_compose_pass(self):
        v.verify(fixture())

    def test_public_port_rejected(self):
        data = fixture()
        data['services']['immich-server']['ports'][0]['host_ip'] = '0.0.0.0'
        with self.assertRaises(ValueError):
            v.verify(data)

    def test_auto_directory_creation_rejected(self):
        data = fixture()
        data['services']['database']['volumes'][0]['bind']['create_host_path'] = True
        with self.assertRaises(ValueError):
            v.verify(data)

    def test_privileged_rejected(self):
        data = fixture()
        data['services']['redis']['privileged'] = True
        with self.assertRaises(ValueError):
            v.verify(data)

    def test_unexpected_version_rejected(self):
        data = fixture()
        data['services']['immich-server']['image'] += '-different'
        with self.assertRaises(ValueError):
            v.verify(data)


if __name__ == '__main__':
    unittest.main()
