本文件与英文 `README.md` 同步维护；以英文版本为准。以下为中文摘要。

# zephyr

`zephyr` 是面向**小型 Go 命令行工具**的项目模板。`puff1` 是 `cmd/puff1/` 下的
示例（类似 `cat`）。可复用代码在 `internal/`；GNU gettext 的 `.po` 在 `po/`，
构建时嵌入二进制（`po/embed.go`）。

## 目录结构

- `cmd/` — 每个可执行文件一个子目录
- `internal/` — 内部分享包（`zephyr` 与 `i18n` 等）
- `po/` — 翻译用 `.po`
- `debian/` — `dpkg-buildpackage` 用元数据
- `meson.build` — 构建、测试、安装与辅助目标

## 构建与测试

**依赖**：Go 1.22+

约定在可用时使用绝对输出目录 `/build`；不可用时可改为其它目录：

```bash
meson setup /build
ninja -C /build
go test ./...
meson test -C /build
```

## 国际化

运行时用 `LANGUAGE` 等环境变量选择 `po/<语言>.po`；翻译文件随可执行文件一起
嵌入。示例：

```bash
LANGUAGE=ja ./build/puff1 -h
```

## 许可

与 `README.md` / `LICENSE` 中的 AGPL-3.0-or-later 及补充说明相同。
