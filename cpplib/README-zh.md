本文件由模板生成。
除项目名称和程序名称外，其余内容均为占位符。
请根据当前项目的具体情况重写此文档。

# zephyr

`zephyr` 是基于 Meson 的 **C++ 共享/静态库** 模板（`cpplib`），并附带示例命令行应用。  
构建 `libzephyr`（共享库与静态库）、安装头文件与 pkg-config，并提供示例应用 `some_puff1`；同一仓库中可以继续添加更多应用。

## 仓库结构

- `src/` - 应用与共享模块源码
- `tests/` - 使用 Check 框架的单元测试（`*_test.cpp` / `*_unit.cpp`）
- `debian/` - Debian 打包元数据
- `docs/` - AsciiDoc man 页源文件（`docs/*.adoc`）
- `meson.build` - 顶层构建定义与辅助目标

## 示例应用：`some_puff1`

`some_puff1` 是一个类似 `cat` 的工具：

```bash
some_puff1 [OPTION]... [FILE]...
```

支持的选项：`-v`/`--verbose`、`-q`/`--quiet`、`-h`/`--help`、`--version`。

## 构建与测试

```bash
sudo apt install meson ninja-build g++ pkg-config check libbas-cpp-dev asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## 许可证

Copyright (C) 2026 Lenik <zephyr@bodz.net>

采用 **AGPL-3.0-or-later** 许可。完整文本见 `LICENSE`。
