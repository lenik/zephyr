# zephyr

`zephyr` 是一个 OCaml 命令行模板，使用 Meson 做构建/测试/安装。  
`some_puff1` 是此模板中的一个**示例应用**；同一仓库中可以继续添加更多应用。

## 仓库结构

- `src/` - OCaml 源码（`*.ml`）
- `tests/` - OCaml 冒烟/单元测试
- `debian/` - Debian 打包元数据
- `po/` - gettext 翻译目录
- `docs/` - AsciiDoc man 页源文件（`docs/*.adoc`）
- `meson.build` - 构建、测试、安装与辅助目标

可选：添加 `dune-project` 以使用 Dune 工作流；Meson 使用 `ocamlfind`/`ocamlc` 编译。

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
sudo apt install meson ninja-build ocaml ocaml-findlib gettext asciidoctor
```

### 配置与构建

使用绝对构建目录 `/build`：

```bash
meson setup /build
ninja -C /build
```

### 运行测试

```bash
meson test -C /build
```

Meson 会运行 `tests/test_commons.ml` 中的 OCaml 冒烟/单元测试。

## i18n (gettext)

`some_puff1` 使用 `po/` 下的 gettext 翻译。

### 同步翻译目录

```bash
ninja -C /build posync
```

## 安装

```bash
meson install -C /build
```

## Debian 包

```bash
dpkg-buildpackage -us -uc
```

## 许可证

Copyright (C) 2026 Lenik <zephyr@bodz.net>

采用 **AGPL-3.0-or-later** 许可证。完整文本见 `LICENSE`。
