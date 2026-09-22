# posync run_target 已外置为 scripts/posync.sh

存在 po/ 时，meson.run_target('posync') 必须调用 scripts/posync.sh，而非内联的 bash -euc heredoc。运行 `zfr ize` 以抽取。

### 内联 posync 难以维护

meson.build 内的 bash -euc heredoc 会在模板间重复且难调试。约定是由 run_target('posync') 接线的 `zfr translate --sync`（Python），而非内联 heredoc。


### 回报

一条命令即可本地同步 xgettext/msgmerge；ninja posync 保持简短；CI 可调用 `zfr translate --sync` 或导入 `translate.sync`。


### Solve

Ize 将 run_target('posync') 重写为通过项目 Python 入口调用 translate --sync（在 zfr 内优先 import）。之后请核对 POTFILES 与语言标志。
