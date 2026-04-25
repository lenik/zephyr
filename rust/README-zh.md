本文件由模板生成。
除项目名称和程序名称外，其余内容均为占位符。
请根据当前项目的具体情况重写此文档。

# zephyr

`zephyr` 是一个以 **Rust（Cargo）** 为主、可选 **Meson** 的中小型命令行应用项目模板。  
`puff1` 是此模板中的一个**示例应用**；同一仓库中可以继续添加更多应用。

## 仓库结构

- `src/` - `zephyr` 库与 `puff1` 可执行文件代码
- `build-aux/cargo-build.sh` - Meson 调用以执行 `cargo build --release`
- `debian/` - Debian 打包元数据
- `meson.build` - man、文档、gettext、`install-symlinks`、以及用 Meson 登记的 `cargo test`
- `Cargo.toml` / `Cargo.lock` - 依赖与锁文件
- `po/` - gettext 翻译

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
sudo apt install build-essential meson ninja-build pkgconf cargo rustup gettext
```

（源码包构建依赖以 `debian/control` 为准。）

### 用 Cargo 构建

```bash
cargo build --release
# ./target/release/puff1
```

### 用 Meson 配置并构建

约定使用**绝对**构建目录 `/build`（若本机可写；否则可换成任意可写目录）：

```bash
meson setup /build
ninja -C /build
```

`ninja` 会执行 `build-aux/cargo-build.sh`，在 `{{builddir}}/cargo-target` 下用 Cargo 完成构建。若需保留 `RUSTC_WRAPPER`（如 sccache），可设置 `ZEPHYR_CARGO_ENABLE_SCCACHE=1`；否则脚本默认会取消该变量。

### 运行测试

```bash
cargo test
# 或
meson test -C /build
```

`meson test` 在构建目录下为 `cargo test` 使用独立的 `target-dir`。

## i18n（gettext）

`puff1` 使用 `po/` 下的 gettext 翻译文件（`*.po` 与生成的 `.mo` 文件）。

- 运行时可用环境变量 `ZEPHYR_LOCALEDIR` 指定「localedir」根目录；未设置时程序会尝试 `build/po` 等开发路径，或回退到 `/usr/local/share/locale`。
- 与常见 gettext 应用一样，从系统正确安装时也会从系统 locale 目录加载翻译。`ninja install-symlinks` 仅做二进制、man 与 bash 补全的符号链接，不负责安装 `.mo` 文件；完整安装请用 `meson install` 或发行版包。`POTFILES` 现为 `src/lib.rs`、`src/main.rs`。

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
LANGUAGE=ja /build/puff1 -h
LANGUAGE=zh_CN /build/puff1 -h
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
