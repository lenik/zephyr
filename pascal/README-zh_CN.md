# zephyr

基于 **Free Pascal** 与 Meson 的 CLI 项目模板。

## 构建

```bash
sudo apt install meson ninja-build fpc asciidoctor
meson setup /build && ninja -C /build && meson test -C /build
```

## 许可

AGPL-3.0-or-later — 见 `LICENSE`。
