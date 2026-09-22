# posync run_target 已外置為 scripts/posync.sh

存在 po/ 時，meson.run_target('posync') 必須呼叫 scripts/posync.sh，而非內聯的 bash -euc heredoc。執行 `zfr ize` 以抽取。

### 內聯 posync 難以維護

meson.build 內的 bash -euc heredoc 會在範本間重複且難除錯。約定是由 run_target('posync') 接線的 `zfr translate --sync`（Python），而非內聯 heredoc。


### 回報

一條指令即可本機同步 xgettext/msgmerge；ninja posync 保持簡短；CI 可呼叫 `zfr translate --sync` 或匯入 `translate.sync`。


### Solve

Ize 將 run_target('posync') 重寫為透過專案 Python 入口呼叫 translate --sync（在 zfr 內優先 import）。之後請核對 POTFILES 與語言旗標。
