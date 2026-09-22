# posync run_target is externalized as scripts/posync.sh

### 内联 posync 难以维护

meson.build 里的 bash -euc heredoc 会在模板间重复，且难调试。约定是由 run_target('posync') 调用 `zfr translate --sync`（Python），而不是内联 heredoc。


### 收益

一条命令在本地同步 xgettext/msgmerge；ninja posync 保持简短；CI 可调用 `zfr translate --sync`，或在 zfr 内 import `translate.sync`。


### Solve

ize 会把 run_target('posync') 改写为通过项目 Python 入口调用 translate --sync（zfr 内部优先 import）。之后请核对 POTFILES 与语言标志。
