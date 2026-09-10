本文件由模板生成。
除项目名称和程序名称外，其余内容均为占位符。
请根据当前项目的具体情况重写此文档。

# zephyr

`zephyr` 是基于 Meson 的最小 **NASM x86-64 Linux** 模板。
`some_puff1` 通过系统调用将标准输入复制到标准输出（类似 `cat`）。

## 仓库结构

- `src/some_puff1.asm` - 主程序
- `src/commons.inc` - 共享常量（缓冲区大小、系统调用号）
- `tests/smoke.sh` - 标准输入/输出冒烟测试
- `meson.build` - `nasm -f elf64` 与 `ld` 链接

## 示例应用：`some_puff1`

```bash
some_puff1 < file
echo hello | some_puff1
```

## 构建

```bash
sudo apt install meson ninja-build nasm asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## 许可证

Copyright (C) 2026 Lenik <zephyr@bodz.net>

采用 **AGPL-3.0-or-later** 许可。完整文本见 `LICENSE`。
