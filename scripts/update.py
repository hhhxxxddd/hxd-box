"""Import Scoop manifests from the projects' published stable GitHub releases."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import stat
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

REPOSITORIES = {
    "dev-tools": "hhhxxxddd/dev-tools",
    "dev-infra": "hhhxxxddd/dev-infra",
}
REQUIRED_FILES = {
    "dev-tools": {"scripts/scoop-entry.ps1", "scripts/scoop.ps1"},
    "dev-infra": {"scripts/dev-infra.ps1", "scripts/install.ps1"},
}
ROOT = Path(__file__).resolve().parents[1]
MAX_PACKAGE_BYTES = 64 * 1024 * 1024


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "hxd-box"})
    limit = MAX_PACKAGE_BYTES if url.endswith(".zip") else 1024 * 1024
    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read(limit + 1)
    if len(content) > limit:
        raise ValueError("下载内容超过允许大小")
    return content


def published_manifest(app: str, *, fetch=download) -> dict | None:
    repository = REPOSITORIES[app]
    try:
        release = json.loads(
            fetch(f"https://api.github.com/repos/{repository}/releases/latest")
        )
    except urllib.error.HTTPError as error:
        error.close()
        if error.code == 404:
            return None
        raise
    if not isinstance(release, dict):
        raise TypeError("发行信息必须为 JSON 对象")
    tag = release.get("tag_name", "")
    if (
        not isinstance(tag, str)
        or not re.fullmatch(r"v\d+\.\d+\.\d+", tag)
        or release.get("draft") is not False
        or release.get("prerelease") is not False
    ):
        raise ValueError("只接受已发布的正式版本")
    version = tag[1:]
    base = f"https://github.com/{repository}/releases/download/{tag}"
    archive = f"{app}-{version}.zip"
    names = (f"{app}.json", "SHA256SUMS", archive)
    assets = release.get("assets", [])
    if not isinstance(assets, list) or not all(
        isinstance(asset, dict) for asset in assets
    ):
        raise ValueError("发行附件列表无效")
    for name in names:
        matches = [asset for asset in assets if asset.get("name") == name]
        if (
            len(matches) != 1
            or matches[0].get("browser_download_url") != f"{base}/{name}"
            or matches[0].get("state") != "uploaded"
        ):
            raise ValueError(f"正式发行附件缺失或无效：{name}")
    manifest = json.loads(fetch(f"{base}/{app}.json"))
    if not isinstance(manifest, dict):
        raise TypeError("清单必须为 JSON 对象")
    checksum = manifest.get("hash", "")
    if (
        manifest.get("version") != version
        or manifest.get("homepage") != f"https://github.com/{repository}"
        or manifest.get("url") != f"{base}/{archive}"
        or not isinstance(checksum, str)
        or not re.fullmatch(r"[0-9a-f]{64}", checksum)
    ):
        raise ValueError("清单版本、来源或 SHA256 无效")
    sums = fetch(f"{base}/SHA256SUMS").decode("ascii")
    matching_hashes = [
        parts[0]
        for line in sums.splitlines()
        if len(parts := line.split()) == 2 and parts[1].lstrip("*") == archive
    ]
    if matching_hashes != [checksum]:
        raise ValueError("清单与 SHA256SUMS 不一致")
    payload = fetch(f"{base}/{archive}")
    if hashlib.sha256(payload).hexdigest() != checksum:
        raise ValueError("发行包 SHA256 校验失败")
    required = REQUIRED_FILES[app] | {".release.json", "pyproject.toml", "LICENSE"}
    with zipfile.ZipFile(io.BytesIO(payload)) as package:
        entries = package.infolist()
        names = [entry.filename for entry in entries]
        if len({name.casefold() for name in names}) != len(names):
            raise ValueError("发行包存在重复或大小写冲突路径")
        if any(
            name.startswith("/")
            or re.search(r'[\\<>:"|?*\x00-\x1f]', name)
            or any(part in {"", ".", ".."} for part in name.rstrip("/").split("/"))
            for name in names
        ):
            raise ValueError("发行包包含无效路径")
        if any(
            stat.S_IFMT(entry.external_attr >> 16)
            not in {0, stat.S_IFREG, stat.S_IFDIR}
            for entry in entries
        ):
            raise ValueError("发行包包含符号链接或特殊文件")
        files = {
            entry.filename
            for entry in entries
            if not entry.is_dir()
            and stat.S_IFMT(entry.external_attr >> 16) in {0, stat.S_IFREG}
        }
        if not required.issubset(files):
            raise ValueError("发行包缺少 Scoop 安装所需文件")
        if sum(entry.file_size for entry in entries) > MAX_PACKAGE_BYTES:
            raise ValueError("发行包解压大小超过允许范围")
        if package.testzip() is not None:
            raise ValueError("发行包文件校验失败")
    return manifest


def write_manifest(app: str, manifest: dict, *, root: Path = ROOT) -> bool:
    if app not in REPOSITORIES:
        raise ValueError("未知软件")
    target = root / "bucket" / f"{app}.json"
    if target.exists():
        current = json.loads(target.read_text(encoding="utf-8"))
        if current == manifest:
            return False
        current_version = current["version"]
        if not re.fullmatch(r"\d+\.\d+\.\d+", current_version):
            raise ValueError("现有清单版本无效")
        old = tuple(map(int, current_version.split(".")))
        new = tuple(map(int, manifest["version"].split(".")))
        if new <= old:
            raise ValueError("拒绝降级或替换同版本的清单")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=target.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(manifest, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
        temporary_path.replace(target)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="从正式发行包更新 hxd-box 软件清单")
    parser.add_argument("apps", nargs="*", help="dev-tools / dev-infra；省略时检查两者")
    arguments = parser.parse_args()
    apps = list(dict.fromkeys(arguments.apps or REPOSITORIES))
    if unknown := set(apps) - REPOSITORIES.keys():
        parser.error("未知软件：" + ", ".join(sorted(unknown)))
    failed = False
    for app in apps:
        try:
            manifest = published_manifest(app)
            if manifest is None:
                print(f"{app}：尚无公开正式发行，保留现有清单")
                continue
            changed = write_manifest(app, manifest)
            state = "已更新" if changed else "已是最新"
            print(f"{app}：{state}（{manifest['version']}）")
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            RuntimeError,
            zipfile.BadZipFile,
        ) as error:
            if isinstance(error, urllib.error.HTTPError):
                error.close()
            print(f"{app}：更新失败：{error}", file=sys.stderr)
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
