本文件由模板生成。
除项目名称和程序名称外，其余内容均为占位符。
请根据当前项目的具体情况重写此文档。

# zephyr

`zephyr` 是基于 Meson 的 **GNU C 扩展** CLI 模板。
与 plain `c/` 模板类似，但使用 `-std=gnu11` 编译，并演示 GCC 特性
（`__attribute__`、语句表达式、`typeof`）。

## 仓库结构

- `src/some_puff1.c` - 使用 GNU C 扩展的示例 cat 应用
- `src/commons.c` / `src/commons.h` - 共享辅助模块
- `tests/commons_test.c` - 最小单元测试
- `meson.build` - 含 `add_project_arguments('-std=gnu11')` 的 Meson 工程

## 示例应用：`some_puff1`

```bash
some_puff1 [OPTION]... [FILE]...
```

支持 `-v`/`--verbose`、`-q`/`--quiet`、`-h`/`--help`、`--version`。

## 构建

```bash
sudo apt install meson ninja-build gcc pkg-config asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## 许可证

Copyright (C) 2026 Lenik <zephyr@bodz.net>

采用 **AGPL-3.0-or-later** 许可。完整文本见 `LICENSE`。
