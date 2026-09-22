# Build/deploy/maintenance scripts live under scripts/

### メンテ脚本は scripts/ へ

ルートの install-symlinks/deploy は梱包面を散らかします。同期と DESTDIR プレビューは `zfr translate --sync` / `zfr build --look`。


### 検出

ルート *.sh と外出しすべき inline run_target を指摘。


### 移動後

文書と CI を更新。Solve が Meson を scripts/… か zfr に書き換え。
