# PyInstaller 构建指南

本文档提供了在不同操作系统上使用 PyInstaller 直接通过命令行打包 `wr2flomo` 应用的命令。

这些命令整合了原 `WR2Flomo.spec` 文件中的所有配置，让您无需依赖该文件即可完成构建。

## 注意事项

- **运行位置**: 请确保在项目的**根目录**下运行以下命令，以保证所有相对路径（如 `src/`, `resources/`）都能被正确识别。
- **依赖安装**: 在运行命令前，请确保已经通过 `pip install -r requirements.txt` 和 `pip install -r requirements-dev.txt` 安装了所有必要的依赖。

---

## macOS 构建命令

```bash
pyinstaller --name wr2flomo --windowed --icon resources/icons/app.icns --add-data "resources:resources" --add-data "resources/styles/minimalist.qss:resources/styles" --hidden-import "PyQt6.QtCore" --hidden-import "PyQt6.QtWidgets" --hidden-import "PyQt6.QtGui" --runtime-hook "scripts/macos_hook.py" src/main.py
```

### 命令解析

- `--name wr2flomo`: 指定输出的应用名称为 `wr2flomo`。
- `--windowed`: 创建一个无控制台窗口的 GUI 应用。
- `--icon resources/icons/app.icns`: 为应用指定 `.icns` 格式的图标。
- `--add-data "source:destination"`: 将额外的文件或目录打包。冒号是 macOS/Linux 上的路径分隔符。
- `--hidden-import "ModuleName"`: 告知 PyInstaller 打包一些它可能无法自动探测到的隐藏依赖。
- `--runtime-hook "scripts/macos_hook.py"`: 指定一个在应用启动前运行的钩子脚本，用于 macOS 特定的设置。
- `src/main.py`: 指定项目的主入口文件。

---

## Windows 构建命令

```powershell
pyinstaller --name wr2flomo --windowed --icon resources/icons/app.ico --add-data "resources;resources" --add-data "resources/styles/minimalist.qss;resources/styles" --hidden-import "PyQt6.QtCore" --hidden-import "PyQt6.QtWidgets" --hidden-import "PyQt6.QtGui" src/main.py
```

### 命令解析

- 大部分参数与 macOS 版本含义相同。
- `--icon resources/icons/app.ico`: 为应用指定 Windows 平台所需的 `.ico` 格式图标。
- **路径分隔符**: 注意在 Windows 上，`--add-data` 参数的源和目标路径之间使用分号 `;` 分隔，而不是冒号 `:`。
- Windows 构建不需要 `runtime-hook` 脚本。
