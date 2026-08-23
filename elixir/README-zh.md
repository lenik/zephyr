# zephyr

`zephyr` 是一个 Elixir 命令行模板，使用 Meson 做构建/测试/安装。  
`some_puff1` 是此模板中的一个**示例应用**；同一仓库中可以继续添加更多应用。

## 仓库结构

- `src/` - Elixir 源码（`*.ex`）
- `tests/` - Elixir 冒烟/单元测试（`*.exs`）
- `debian/` - Debian 打包元数据
- `po/` - gettext 翻译目录
- `docs/` - AsciiDoc man 页源文件（`docs/*.adoc`）
- `meson.build` - 构建、测试、安装与辅助目标

可选：添加 `mix.exs` 以使用 Mix 工作流；Meson 使用 `elixirc` 编译并安装 escript 风格包装脚本。

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
sudo apt install meson ninja-build elixir gettext asciidoctor
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

Meson 会运行 `tests/test_commons.exs` 中的 Elixir 冒烟/单元测试。

## i18n (gettext)

`some_puff1` 使用 `po/` 下的 gettext 翻译（`*.po` 与生成的 `.mo` 文件）。

Zephyr 风格建议 `po/LINGUAS` 至少覆盖：**ar bn de es fr hi id it ja ko pt ru sv ta te th tr ur vi zh_CN zh_TW**（英文为 msgid 源语言；`zh-cn`/`zh-tw` 对应 `zh_CN`/`zh_TW`）。

### 同步翻译目录

```bash
ninja -C /build posync
```

### 构建翻译文件

```bash
ninja -C /build
```

### 快速 locale 测试

```bash
LANGUAGE=ja /build/some_puff1 -h
LANGUAGE=zh_CN /build/some_puff1 -h
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

采用 **AGPL-3.0-or-later** 许可证。  
本项目明确反对 AI 剥削与 AI 霸权，并拒绝盲目的 MIT 式许可与政治天真的 BSD 式许可。  
完整文本与补充条款见 `LICENSE`。
