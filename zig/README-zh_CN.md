# zephyr

`zephyr` 是一个 **Zig** + Meson 命令行应用项目模板。  
`some_puff1` 是示例应用；共享代码在 `src/commons.zig`。  
`build.zig` 是 Zig 构建清单（类似 Go 的 `go.mod`）。

## 构建与测试

```bash
sudo apt install meson ninja-build zig asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## 许可证

Copyright (C) 2026 Lenik <zephyr@bodz.net>

采用 **AGPL-3.0-or-later** 许可。见 `LICENSE`。
