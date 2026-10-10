# HXD Box

## 0 · 简介

HXD Box 是我的个人 Scoop 软件合集，用来集中分发自己开发的工具和应用。

添加一次软件源，即可通过 Scoop 安装、更新和卸载其中的软件。各项目的源码与发布包仍由各自仓库维护。

## 1 · 快速开始

打开普通权限的 PowerShell，安装 Scoop：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex
```

安装 Git 并添加软件源：

```powershell
scoop install git
scoop bucket add hxd https://github.com/hhhxxxddd/hxd-box
```

已完成的步骤可以跳过。

常用命令：

```powershell
scoop search <软件名>
scoop install hxd/<软件名>
scoop update <软件名>
scoop uninstall <软件名>
```

## 2 · 软件清单

以下先作为规划占位，尚不表示已收录或可安装。

| 软件 | 简介 | 计划包名 |
|---|---|---|
| dev-tools | Windows / WSL 本地开发管理，涵盖项目发现、工具链与开发服务管理 | dev-tools |
| dev-infra | 开发基础设施配置与管理工具，具体功能待补充 | dev-infra |
| 星空馆 · OmniGallery | 素材管理与浏览，结合 AI 图像、音频和视频处理能力 | omnigallery |

后续按各项目的实际发布情况补充安装清单。
