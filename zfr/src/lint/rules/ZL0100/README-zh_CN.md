# scripts/ci 辅助用于多发行版包构建

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
