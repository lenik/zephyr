本文件由模板生成。
除项目名称和程序名称外，其余内容均为占位符。
请根据当前项目的具体情况重写此文档。

# zephyr

`zephyr` 是基于 Meson 的 **C 共享/静态库** 模板（`clib`），并附带示例命令行应用。  
构建 `libzephyr`（共享库与静态库）、安装头文件与 pkg-config，并提供示例应用 `some_puff1`；同一仓库中可以继续添加更多应用。

## 仓库结构

- `src/` - 应用与共享模块源码
- `tests/` - 使用 Check 框架的单元测试（`*_unit.c`）
- `debian/` - Debian 打包元数据
- `docs/` - AsciiDoc man 页源文件（`docs/*.adoc`）
- `meson.build` - 顶层构建定义与辅助目标

## 示例应用：`some_puff1`

`some_puff1` 是一个类似 `cat` 的工具：

```bash
some_puff1 [OPTION]... [FILE]...
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
sudo apt install meson ninja-build gcc pkg-config check asciidoctor
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

Meson 会自动发现 `tests/*_unit.c` 中的单元测试并完成注册。

## i18n（gettext）

`some_puff1` 使用 `po/` 下的 gettext 翻译文件（`*.po` 与生成的 `.mo` 文件）。

Zephyr 风格建议 `po/LINGUAS` 至少包含：**ar bn de es fr hi id it ja ko pt ru sv
ta te th tr ur vi zh_CN zh_TW**（英文为 msgid 源语言；`zh-cn`/`zh-tw` 对应
`zh_CN`/`zh_TW`）。

- 安装后运行时从系统 locale 目录加载翻译。
- 开发态运行（`/build/some_puff1`）若存在 `/build/po`，会优先使用项目内翻译资源。

### 同步翻译词条

使用 `posync` 从当前源码字符串同步词条：

```bash
ninja -C /build posync
```

`posync` 会：

- 为 `po/LINGUAS` 中每种语言补齐缺失消息
- 移除源码中已不再使用的废弃消息

### 构建翻译文件

```bash
ninja -C /build
```

### 快速测试语言

建议优先使用 `LANGUAGE=<lang>`，在开发环境中选择更稳定：

```bash
LANGUAGE=ja /build/some_puff1 -h
LANGUAGE=zh_CN /build/some_puff1 -h
```

`LANG=<lang>.<encoding>` 是否生效取决于系统是否已生成对应 locale。

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
