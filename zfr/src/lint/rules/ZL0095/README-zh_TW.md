# posync run_target is externalized as scripts/posync.sh

### 內聯 posync 難以維護

meson.build 裡的 bash -euc heredoc 會在模板間重複，且難調試。約定是由 run_target('posync') 調用 `zfr translate --sync`（Python），而不是內聯 heredoc。


### 收益

一條命令在本地同步 xgettext/msgmerge；ninja posync 保持簡短；CI 可調用 `zfr translate --sync`，或在 zfr 內 import `translate.sync`。


### Solve

ize 會把 run_target('posync') 改寫為通過項目 Python 入口調用 translate --sync（zfr 內部優先 import）。之後請核對 POTFILES 與語言標誌。
