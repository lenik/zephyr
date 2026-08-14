本文件由模板生成。
除项目名称和程序名称外，其余内容均为占位符。
请根据当前项目的具体情况重写此文档。

# zephyr

`zephyr` 是基于 Meson 与 [bash-shlib](http://uni.bodz.net/base/bash-shlib)（`import cliboot`）的 **Bash** 命令行模板。  
示例脚本为 `src/some_puff1`。

## 构建 / 安装

```bash
sudo apt install meson ninja-build asciidoctor bash-shlib
meson setup /build
ninja -C /build
meson install -C /build
```

## 示例

```bash
some_puff1 [OPTION]... [FILE]...
```

## 许可证

Copyright (C) 2026 Lenik <zephyr@bodz.net> — **AGPL-3.0-or-later**。见 `LICENSE`。
