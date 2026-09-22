# posync run_target is externalized as scripts/posync.sh

### インライン posync は保守不能

meson.build 内の bash -euc heredoc はテンプレ間で重複しデバッグ困難。契約は run_target('posync') からの `zfr translate --sync`。


### 利点

1コマンドで xgettext/msgmerge。ninja posync は短く、CI は `zfr translate --sync` か import。


### Solve

ize は posync を translate --sync に付け替えます。POTFILES を確認。
