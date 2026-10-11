# Manifest maintenance

[简体中文](maintenance.md)

Users only need Scoop and Git. The Python commands below are for bucket maintenance and use Python 3.14.

Each project's stable Release provides a ZIP, `SHA256SUMS`, and `<app>.json` for the same version. Run from the repository directory:

```powershell
python scripts/update.py
# Or update one application
python scripts/update.py dev-tools
python scripts/update.py dev-infra
```

The script imports manifests from the official repositories' latest public stable Releases. It checks versions, download URLs, SHA256 hashes, and installation entrypoints before writing to `bucket/`. It does not execute packages, replace different manifests for the same version, or downgrade versions.

Applications without a public stable Release are skipped, preserving existing manifests without creating uninstallable placeholders. After dev-infra's first public Release, run the same command to create `bucket/dev-infra.json`.

Review, commit, and push manifest changes; users receive them through `scoop update`. hxd-box itself needs no Release. For public distribution, both the bucket repository and the packages referenced by its manifests must be publicly accessible.

Run the offline tests after changing the maintenance script:

```powershell
python -m unittest discover -v tests
```
