## ZL0001

### 長いファイルは所有を妨げる

非常に長いソースはレビュー・テスト・所有が難しいです。Zephyr はパッケージ配下のまとまったモジュールと薄い入口を好みます。


### 改善の利点

小さいレビュー差分、明確な境界、単体テストしやすさ、マージ衝突の減少。


### しきい値

空でない行を数えます（build/debian/po/… 除外）。約600で note、約1000で warn。テンプレ例は除外。


### 修正は手動

分割し meson/install/import を更新。`zfr ize` は自動分割しません。


## ZL0095
### インライン posync は保守不能

meson.build 内の bash -euc heredoc はテンプレ間で重複しデバッグ困難。契約は run_target('posync') からの `zfr translate --sync`。


### 利点

1コマンドで xgettext/msgmerge。ninja posync は短く、CI は `zfr translate --sync` か import。


### Solve

ize は posync を translate --sync に付け替えます。POTFILES を確認。


## ZL0096
### メンテ脚本は scripts/ へ

ルートの install-symlinks/deploy は梱包面を散らかします。同期と DESTDIR プレビューは `zfr translate --sync` / `zfr build --look`。


### 検出

ルート *.sh と外出しすべき inline run_target を指摘。


### 移動後

文書と CI を更新。Solve が Meson を scripts/… か zfr に書き換え。
