本文件由模板生成。
除项目名称和程序名称外，其余内容均为占位符。
请根据当前项目的具体情况重写此文档。

# zephyr

`zephyr` 是基于 Meson 的 **ANTLR4 解析器 CLI** 模板。
`some_puff1` 解析简单 s-表达式，例如 `(hello world)` 或 `(add 1 2)`。

## 仓库结构

- `src/SomePuff1.g4` - ANTLR4 语法（启用 visitor 生成）
- `src/Main.java` - CLI 入口
- `src/commons.java` - AST 转储/格式化辅助模块
- `tests/` - Java commons 测试
- `meson.build` - 调用 `antlr4 -visitor`、`javac` 并安装 jar 启动器

## 示例应用：`some_puff1`

```bash
some_puff1 [OPTION]... [FILE]...
```

解析器选项与 Bison 模板一致：`--dump`、`--format`、`--indent-size`、`--color`、`--help`、`--version`。

## 构建

```bash
sudo apt install meson ninja-build default-jdk antlr4 libantlr4-runtime-java asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## 许可证

Copyright (C) 2026 Lenik <zephyr@bodz.net>

采用 **AGPL-3.0-or-later** 许可。完整文本见 `LICENSE`。
