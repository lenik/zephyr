# zephyr

`zephyr` 是一个 **Lua** + Meson 命令行应用项目模板。  
`some_puff1` 是此模板中的一个**示例应用**。

## 仓库结构

- `src/` - Lua 源码（示例 `some_puff1.lua` 与共享辅助模块 `commons.lua`）
- `tests/` - Lua 单元测试
- `docs/` - AsciiDoc man 页源文件
- `meson.build` - 安装、测试与辅助目标

## 示例应用：`some_puff1`

类似 `cat` 的工具，支持 `-v`、`-q`、`-h`、`--version` 等选项。

## 构建与测试

```bash
sudo apt install meson ninja-build lua5.4 luajit asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## 许可证

Copyright (C) 2026 Lenik <zephyr@bodz.net>

采用 **AGPL-3.0-or-later** 许可。完整文本见 `LICENSE`。
