# VERSION 与 debian/changelog 一致

### 单一事实来源

`VERSION` 应与最新的 `debian/changelog` 条目一致。标准 `.githooks/pre-commit`（配合 `core.hooksPath=.githooks`）会在提交时从 changelog 重写 `VERSION`。


### 已配置同步钩子时

若该 pre-commit 钩子存在且会从 changelog 同步 VERSION，则在下次提交前出现短暂不一致是预期的——lint 报告 **ok** 而非警告。


### 未配置钩子时

不一致为 **warn**：请手工对齐 VERSION，或通过 `zfr ize` 安装标准钩子，再执行 `git config core.hooksPath .githooks`。
