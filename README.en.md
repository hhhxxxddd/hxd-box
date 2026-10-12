# hxd-box

[简体中文](README.md) · **English**

[![Scoop](https://img.shields.io/badge/Scoop-bucket-blue)](https://scoop.sh/)

A personal Scoop bucket for installation manifests of my tools and applications. Source code and release assets are maintained in each project's repository.

## Usage

On Windows, install Scoop using the [official instructions](https://github.com/ScoopInstaller/Install#installation) and run it from a non-administrator PowerShell session.

Add the bucket and install the tools you need; skip the first line if Git is already installed:

```powershell
scoop install git
scoop bucket add hxd-box https://github.com/hhhxxxddd/hxd-box
scoop install hxd-box/dev-tools
scoop install hxd-box/dev-infra
```

See each project's README for its system requirements and dependencies.

## Package roadmap

| Project | Purpose | Planned package | Available |
| --- | --- | --- | --- |
| [dev-tools](https://github.com/hhhxxxddd/dev-tools) | Hot deployment and live updates for Windows / WSL development projects | `dev-tools` | [v0.5.1](https://github.com/hhhxxxddd/dev-tools/releases/tag/v0.5.1) |
| [dev-infra](https://github.com/hhhxxxddd/dev-infra) | Local development middleware, ready out of the box | `dev-infra` | [v0.3.0](https://github.com/hhhxxxddd/dev-infra/releases/tag/v0.3.0) |
| [星空馆 · OmniGallery](https://github.com/hhhxxxddd/omnigallery) | Collect, create and edit images, audio and video, with AI tools for creation and editing | `omnigallery` | Not yet |

## Common commands

Using `dev-tools` as an example:

```powershell
# Search
scoop search dev-tools

# Refresh Scoop and manifests, then update the application
scoop update
scoop update dev-tools

# Uninstall the application
scoop uninstall dev-tools
```

For more commands, see the [Scoop quick start](https://github.com/ScoopInstaller/Scoop/wiki/Quick-Start).

See [manifest maintenance](docs/maintenance.en.md) for adding and updating packages.
