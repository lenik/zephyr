# ビルド/デプロイ/メンテ用スクリプトは scripts/ 配下

ルートの *.sh ヘルパーと look / install-symlinks / uninstall-symlinks / posync / deploy の meson run_target 本体は scripts/ に置きます。移動と再配線には `zfr ize`。

### メンテ用スクリプトは scripts/ 配下

リポジトリ根の install-symlinks / deploy ヘルパーはパッケージング表面を散らかします。Zephyr はそれらを scripts/ に置きます。カタログ同期と DESTDIR プレビューは可能なら専用 posync.sh/look.sh ではなく `zfr translate --sync` と `zfr build --look`。


### 検出

ルートのメンテ用 *.sh 名と、外出しまたは zfr サブコマンドへの置換が必要なインライン run_target 本体にフラグを立てます。


### 移動後

ドキュメントと旧パスを呼ぶ CI を更新。Solve は Meson run_target を scripts/… または zfr translate/build へ書き換えます。
