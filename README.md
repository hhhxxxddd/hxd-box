# hxd-box

**简体中文** · [English](README.en.md)

[![Scoop](https://img.shields.io/badge/Scoop-bucket-blue)](https://scoop.sh/)

个人 Scoop 软件源，集中维护自研工具和应用的安装清单。源码与发行包由各项目仓库维护。

## 使用

在 Windows 上按 [Scoop 官方说明](https://github.com/ScoopInstaller/Install#installation)安装 Scoop，使用普通权限的 PowerShell。

添加软件源后按需安装工具；已有 Git 时可跳过第一行：

```powershell
scoop install git
scoop bucket add hxd-box https://github.com/hhhxxxddd/hxd-box
scoop install hxd-box/dev-tools
scoop install hxd-box/dev-infra
```

各应用的系统版本与依赖要求见对应项目的 README。

## 收录计划

| 项目 | 用途 | 计划包名 | 上线 |
| --- | --- | --- | --- |
| [dev-tools](https://github.com/hhhxxxddd/dev-tools) | Windows / WSL 开发项目的热部署与热更新 | `dev-tools` | [v0.5.3](https://github.com/hhhxxxddd/dev-tools/releases/tag/v0.5.3) |
| [dev-infra](https://github.com/hhhxxxddd/dev-infra) | 开箱即用的本地开发中间件 | `dev-infra` | [v0.3.0](https://github.com/hhhxxxddd/dev-infra/releases/tag/v0.3.0) |
| [星空馆 · OmniGallery](https://github.com/hhhxxxddd/omnigallery) | 图像、音频、视频的收藏、创作与编辑，支持 AI 创作与编辑 | `omnigallery` | 未上线 |

## 常用命令

以 `dev-tools` 为例：

```powershell
# 搜索
scoop search dev-tools

# 刷新 Scoop 与软件清单，再更新应用
scoop update
scoop update dev-tools

# 卸载应用
scoop uninstall dev-tools
```

更多用法见 [Scoop 使用指南](https://github.com/ScoopInstaller/Scoop/wiki/Quick-Start)。

清单收录与更新见[维护说明](docs/maintenance.md)。
