# zephyr

`zephyr` 是一个 C# 命令行模板，使用 Meson 做构建/测试/安装。  
`puff1` 是此模板中的一个**示例应用**；同一仓库中可以继续添加更多应用。

## 仓库结构

- `lib/Zephyr/` - 公共类库（`Zephyr.csproj`、`common_lib.cs` 等）
- `apps/Puff1/` - 示例命令行（`Puff1.csproj`、`Program.cs`、`Resources/*.resx`）
- `tests/` - C# 冒烟/单元测试
- `debian/` - Debian 打包元数据
- `scripts/emit-strings-resx.py` - 可选：根据脚本内词条表重生成 `apps/Puff1/Resources/Strings*.resx`
- `zephyr.sln` - 解决方案（类库 + Puff1 + 测试），可用 Visual Studio 或 `dotnet build` 打开
- `meson.build` - 构建、测试、安装与辅助目标

## 示例应用：`puff1`

`puff1` 是一个类似 `cat` 的工具：

```bash
puff1 [OPTION]... [FILE]...
```

- 如果未提供 `FILE`，则从 `stdin` 读取。
- 如果某个 `FILE` 为 `-`，则在该位置从 `stdin` 读取。
- 输出写入 `stdout`。

支持的选项：

- `-v`, `--verbose`
- `-q`, `--quiet`
- `-h`, `--help`
- `--version`

## 构建与测试

### 构建依赖

```bash
sudo apt install meson ninja-build dotnet-sdk-8.0
```

### 配置并构建

使用绝对构建目录 `/build`：

```bash
meson setup /build
ninja -C /build
```

### 运行测试

```bash
meson test -C /build
```

Meson 执行 `tests/TestCommonLib.csproj` 做冒烟/单元测试。

## 本地化（.resx）

`puff1` 在 `apps/Puff1/Resources/` 下使用内嵌 `.resx`：默认 `Strings.resx`，各文化为 `Strings.<文化>.resx`，构建后在主程序集旁生成附属资源程序集。

- 语言选择使用环境变量 `LC_ALL` / `LC_MESSAGES` / `LANG`（与常见 Unix 习惯一致），例如 `LANG=de_DE.UTF-8 /build/puff1 -h`、`LANG=zh-CN.UTF-8 /build/puff1 -h`。

### 从词条表重生成 `*.resx`（可选）

在 `apps/Puff1/Resources/Strings.resx` 中增加键后，可在 `scripts/emit-strings-resx.py` 的表里补翻译并执行：

```bash
python3 scripts/emit-strings-resx.py
```

再重新构建以更新附属程序集。

## 安装 / 符号链接辅助命令

常规安装：

```bash
meson install -C /build
```

调试符号链接工作流（在已配置的安装前缀下）：

```bash
ninja -C /build install-symlinks
ninja -C /build uninstall-symlinks
```

## Debian 打包

```bash
dpkg-buildpackage -us -uc
```

## 许可证

Copyright (C) 2026 Lenik <zephyr@bodz.net>

采用 **AGPL-3.0-or-later** 许可。  
本项目明确反对 AI 剥削与 AI 霸权，反对无脑 MIT 式许可证和政治愚蠢的 BSD 式许可证。  
完整文本及项目补充条款见 `LICENSE`。
