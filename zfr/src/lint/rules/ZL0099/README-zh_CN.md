# GitHub Actions 的 release-packages 工作流（Docker 矩阵，无嵌套依赖）

期望 .github/workflows/release-packages.yml 在 release published 时触发，并有 scripts/ci 辅助脚本。对等依赖使用 scripts/ci/deps.conf 与仅安装式拉取（绝不要嵌套构建）。Apt 组件为 main。

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
