# 清单维护

[English](maintenance.en.md)

用户通过 Scoop 安装应用，系统与运行依赖见各项目 README；以下 Python 命令仅用于维护此仓库，使用 Python 3.14。

各项目的正式 Release 提供同版本 ZIP、`SHA256SUMS` 和 `<软件名>.json`。在仓库目录执行：

```powershell
python scripts/update.py
# 或只更新一个软件
python scripts/update.py dev-tools
python scripts/update.py dev-infra
```

脚本从官方仓库的最新公开正式 Release 读取清单，核对版本、下载地址、SHA256 和安装入口后写入 `bucket/`；不执行安装包。不覆盖同版本的不同清单，也不降级。

dev-tools 和 dev-infra 发布新版本后，运行上述命令同步清单。尚无公开正式 Release 的软件会被跳过并保留已有清单，不创建不可安装的占位文件。

检查改动后提交并推送清单，用户执行 `scoop update` 即可获取。hxd-box 自身无需发布 Release。公开分发时，bucket 仓库与清单指向的安装包均须可公开访问。

修改维护脚本后可运行离线测试：

```powershell
python -m unittest discover -v tests
```
