# zephyr

`zephyr` 是一个 **Kotlin** + Meson 命令行应用项目模板。  
`some_puff1` 是此模板中的示例应用。

## 仓库结构

- `src/` - Kotlin 源码（`Main.kt` 与 `commons.kt`）
- `tests/` - Kotlin 单元/冒烟测试
- `build.gradle.kts` - 可选 Gradle 标记文件（实际构建使用 Meson）
- `meson.build` - 构建、测试与安装规则

## 构建与测试

```bash
sudo apt install meson ninja-build kotlin default-jdk asciidoctor
meson setup /build
ninja -C /build
meson test -C /build
```

## 许可证

Copyright (C) 2026 Lenik <zephyr@bodz.net>

采用 **AGPL-3.0-or-later** 许可。见 `LICENSE`。
