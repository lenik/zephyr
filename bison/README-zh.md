本文件由模板生成。
除项目名称和程序名称外，其余内容均为占位符。
请根据当前项目的具体情况重写此文档。

# zephyr

`zephyr` 是基于 Meson 的 **Bison/Flex 解析器 CLI** 模板。
`some_puff1` 解析简单 s-表达式，例如 `(hello world)` 或 `(add 1 2)`。

## 仓库结构

- `src/` - Flex 词法器、Bison 语法、主程序与 AST 辅助模块
- `tests/` - 基于样例输入/期望输出的测试
- `docs/` - AsciiDoc man 页源文件
- `meson.build` - 调用 flex/bison 并用 gcc 链接

## 示例应用：`some_puff1`

```bash
some_puff1 [OPTION]... [FILE]...
```

- `-d, --dump` — AST 转储
- `-f, --format` — 格式化重写（默认）
- `--indent-size NUM` — 缩进宽度（默认 4）
- `-C, --color MODE` — `auto|always|never`（默认 auto）
- `-h, --help`、`--version`

## 构建

```bash
sudo apt install meson ninja-build gcc flex bison pkg-config asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## 许可证

Copyright (C) 2026 Lenik <zephyr@bodz.net>

采用 **AGPL-3.0-or-later** 许可。完整文本见 `LICENSE`。
