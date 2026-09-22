# VERSION 與 debian/changelog 一致

### 單一事實來源

`VERSION` 應與最新的 `debian/changelog` 條目一致。標準 `.githooks/pre-commit`（配合 `core.hooksPath=.githooks`）會在提交時從 changelog 重寫 `VERSION`。


### 已設定同步 hook 時

若該 pre-commit hook 存在且會從 changelog 同步 VERSION，則在下次提交前出現短暫不一致是預期的——lint 報告 **ok** 而非警告。


### 未設定 hook 時

不一致為 **warn**：請手動對齊 VERSION，或透過 `zfr ize` 安裝標準 hook，再執行 `git config core.hooksPath .githooks`。
