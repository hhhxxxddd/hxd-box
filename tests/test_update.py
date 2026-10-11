import hashlib
import io
import json
import tempfile
import unittest
import urllib.error
import warnings
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import update


class ManifestUpdateTests(unittest.TestCase):
    def fixture(self, app="dev-tools", version="0.4.1", missing_file=None):
        repository = update.REPOSITORIES[app]
        archive = f"{app}-{version}.zip"
        base = f"https://github.com/{repository}/releases/download/v{version}"
        output = io.BytesIO()
        required = update.REQUIRED_FILES[app] | {
            ".release.json",
            "pyproject.toml",
            "LICENSE",
        }
        with zipfile.ZipFile(output, "w") as package:
            for name in sorted(required - {missing_file}):
                package.writestr(name, "fixture")
        payload = output.getvalue()
        checksum = hashlib.sha256(payload).hexdigest()
        manifest = {
            "version": version,
            "homepage": f"https://github.com/{repository}",
            "url": f"{base}/{archive}",
            "hash": checksum,
            "bin": [[min(update.REQUIRED_FILES[app]), app]],
            "installer": {"script": "preserve upstream hook"},
        }
        release = {
            "tag_name": f"v{version}",
            "draft": False,
            "prerelease": False,
            "assets": [
                {
                    "name": name,
                    "browser_download_url": f"{base}/{name}",
                    "state": "uploaded",
                }
                for name in (f"{app}.json", "SHA256SUMS", archive)
            ],
        }
        urls = {
            f"https://api.github.com/repos/{repository}/releases/latest": json.dumps(
                release
            ).encode(),
            f"{base}/{app}.json": json.dumps(manifest).encode(),
            f"{base}/SHA256SUMS": f"{checksum}  {archive}\n".encode(),
            f"{base}/{archive}": payload,
        }
        return manifest, release, urls

    def test_imports_both_projects_without_rewriting_hooks(self):
        for app in update.REPOSITORIES:
            with self.subTest(app=app):
                manifest, _, urls = self.fixture(app)
                self.assertEqual(
                    update.published_manifest(app, fetch=urls.__getitem__), manifest
                )

    def test_no_public_release_skips_but_other_http_failures_raise(self):
        for status in (404, 403, 500):
            with self.subTest(status=status):

                def fetch(url, code=status):
                    error = urllib.error.HTTPError(url, code, "fixture", {}, None)
                    error.close()
                    raise error

                if status == 404:
                    self.assertIsNone(
                        update.published_manifest("dev-infra", fetch=fetch)
                    )
                else:
                    with self.assertRaises(urllib.error.HTTPError):
                        update.published_manifest("dev-infra", fetch=fetch)

    def test_rejects_wrong_json_types(self):
        for change in ("release", "assets", "asset", "manifest"):
            with self.subTest(change=change):
                manifest, release, urls = self.fixture()
                api_url = next(iter(urls))
                if change == "release":
                    urls[api_url] = b"[]"
                elif change in ("assets", "asset"):
                    release["assets"] = {} if change == "assets" else [None]
                    urls[api_url] = json.dumps(release).encode()
                else:
                    urls[manifest["url"].rsplit("/", 1)[0] + "/dev-tools.json"] = b"[]"
                with self.assertRaises((ValueError, TypeError)):
                    update.published_manifest("dev-tools", fetch=urls.__getitem__)

    def test_rejects_wrong_release_and_asset_identity(self):
        for change in ("prerelease", "draft", "tag", "missing_asset", "foreign_url"):
            with self.subTest(change=change):
                _, release, urls = self.fixture()
                api_url = next(iter(urls))
                if change in ("prerelease", "draft"):
                    release[change] = True
                elif change == "tag":
                    release["tag_name"] = "v0.4.1/other"
                elif change == "missing_asset":
                    release["assets"].pop()
                else:
                    release["assets"][0]["browser_download_url"] = (
                        "https://example.com/app.json"
                    )
                urls[api_url] = json.dumps(release).encode()
                with self.assertRaises(ValueError):
                    update.published_manifest("dev-tools", fetch=urls.__getitem__)

    def test_rejects_manifest_or_download_corruption(self):
        for change in ("version", "url", "hash", "checksum", "zip"):
            with self.subTest(change=change):
                manifest, _, urls = self.fixture()
                manifest_url = manifest["url"].rsplit("/", 1)[0] + "/dev-tools.json"
                if change == "version":
                    manifest["version"] = "0.5.0"
                elif change == "url":
                    manifest["url"] = "https://example.com/package.zip"
                elif change == "hash":
                    manifest["hash"] = "0" * 64
                elif change == "checksum":
                    urls[manifest_url.rsplit("/", 1)[0] + "/SHA256SUMS"] = b"invalid"
                else:
                    urls[manifest["url"]] += b"corruption"
                urls[manifest_url] = json.dumps(manifest).encode()
                with self.assertRaises(ValueError):
                    update.published_manifest("dev-tools", fetch=urls.__getitem__)

    def test_rejects_package_without_installation_entrypoint(self):
        _, _, urls = self.fixture(missing_file="scripts/scoop-entry.ps1")
        with self.assertRaisesRegex(ValueError, "安装所需文件"):
            update.published_manifest("dev-tools", fetch=urls.__getitem__)

    def test_rejects_unsafe_zip_paths_and_links(self):
        for name, mode in (
            ("../escape", 0o100644),
            ("LICENSE", 0o100644),
            ("license", 0o100644),
            ("link", 0o120777),
        ):
            with self.subTest(name=name):
                manifest, _, urls = self.fixture()
                output = io.BytesIO(urls[manifest["url"]])
                with (
                    warnings.catch_warnings(action="ignore", category=UserWarning),
                    zipfile.ZipFile(output, "a") as package,
                ):
                    entry = zipfile.ZipInfo(name)
                    entry.external_attr = mode << 16
                    package.writestr(entry, "fixture")
                payload = output.getvalue()
                checksum = hashlib.sha256(payload).hexdigest()
                manifest["hash"] = checksum
                base = manifest["url"].rsplit("/", 1)[0]
                urls[f"{base}/dev-tools.json"] = json.dumps(manifest).encode()
                urls[f"{base}/SHA256SUMS"] = (
                    f"{checksum}  dev-tools-0.4.1.zip\n".encode()
                )
                urls[manifest["url"]] = payload
                with self.assertRaises(ValueError):
                    update.published_manifest("dev-tools", fetch=urls.__getitem__)

    def test_atomic_update_and_same_version_conflict(self):
        manifest, _, _ = self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertTrue(update.write_manifest("dev-tools", manifest, root=root))
            target = root / "bucket/dev-tools.json"
            previous = target.read_bytes()
            self.assertFalse(update.write_manifest("dev-tools", manifest, root=root))
            altered = manifest | {"hash": "0" * 64}
            with self.assertRaises(ValueError):
                update.write_manifest("dev-tools", altered, root=root)
            self.assertEqual(target.read_bytes(), previous)
            newer = manifest | {"version": "0.5.0"}
            with (
                patch.object(Path, "replace", side_effect=OSError("fixture failure")),
                self.assertRaises(OSError),
            ):
                update.write_manifest("dev-tools", newer, root=root)
            self.assertEqual(target.read_bytes(), previous)
            self.assertEqual(list(target.parent.iterdir()), [target])
            with (
                patch.object(json, "dump", side_effect=OSError("fixture failure")),
                self.assertRaises(OSError),
            ):
                update.write_manifest("dev-tools", newer, root=root)
            self.assertEqual(target.read_bytes(), previous)
            self.assertEqual(list(target.parent.iterdir()), [target])

    def test_rejects_downgrade(self):
        manifest, _, _ = self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            update.write_manifest("dev-tools", manifest, root=root)
            with self.assertRaises(ValueError):
                update.write_manifest(
                    "dev-tools", manifest | {"version": "0.4.0"}, root=root
                )

    def test_failed_application_does_not_block_other_application(self):
        for error in (ValueError("invalid release"), RuntimeError("encrypted ZIP")):
            with (
                self.subTest(error=type(error).__name__),
                patch.object(update.sys, "argv", ["update.py"]),
                patch.object(
                    update, "published_manifest", side_effect=[error, None]
                ) as fetch,
                patch.object(update, "write_manifest") as write,
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(update.main(), 1)
                self.assertEqual(fetch.call_count, 2)
                write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
