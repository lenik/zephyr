# RPM CI 映射 Debian Build-Depends；仅 RPM 的补丁通过 %patch

当把 debian/control 的 Build-Depends 转成 rpmbuild 时，按经验映射：bash-builtins → bash（提供 bash.pc）。仅 RPM 的源码调整放在 packaging/rpm/*.patch，用 PatchN + %autosetup/%patch 应用（build-rpm 复制到 SOURCES）；不要在容器里改动系统 .pc 文件。

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
