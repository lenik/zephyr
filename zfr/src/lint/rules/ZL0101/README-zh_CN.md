# CI 矩阵架构策略（debian armhf/v7；raspi armhf/v6；uos/kylin loong64）

Debian armhf 使用 linux/arm/v7；raspi_* 使用 linux/arm/v6。loong64 仅用于 uos_*/kylin_*。Ubuntu 可能增加 i386/amd64v3；另有 mingw/cygwin 矩阵段用于 Windows 原生构建。

### {title}

规则 {id}（`{code}`）属于 zephyr packaging/
布局约定。默认严重级别提示：{sev}。

### lint 做什么

{detail}
在 `zfr lint` 中由 `{code}` 实现。尽可能附带
具体修复说明。可用 `-w` / `-e` / `--strict` 重映射严重级别。

### 改动树时

修复可能触及 packaging、meson.build、源码或脚手架
副本。上传前请 diff Maintainer、Depends、%files 与 *.in 脚本。
