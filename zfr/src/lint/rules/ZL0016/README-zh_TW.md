# VERSION 與 debian/changelog 一致

### 單一事實來源

`VERSION` 應與最新的 `debian/changelog` 條目一致。標準 `.githooks/pre-commit`（配合 `core.hooksPath=.githooks`）會在提交時重寫 `VERSION`。


### 已設定同步鉤子時

若該 pre-commit 鉤子存在且從 changelog 同步 VERSION，則下次提交前的暫時不一致是預期的——lint 報告 **ok** 而非警告。


### 未設定鉤子時

不一致為 **warn**：手動對齊 VERSION，或透過 `zfr ize` 安裝標準鉤子，然後 `git config core.hooksPath .githooks`。
