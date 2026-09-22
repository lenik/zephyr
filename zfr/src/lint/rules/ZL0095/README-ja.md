# posync の run_target が scripts/posync.sh に外出し済み

po/ があるとき、meson.run_target('posync') はインラインの bash -euc heredoc ではなく scripts/posync.sh を呼ぶ必要があります。抽出には `zfr ize` を実行。

### インライン posync は保守不能

meson.build 内の bash -euc heredoc はテンプレート間で重複し、デバッグが苦痛です。契約は run_target('posync') から配線した `zfr translate --sync`（Python）であり、インライン heredoc ではありません。


### 見返り

一つのコマンドで xgettext/msgmerge をローカル同期；ninja posync は短く保たれ；CI は `zfr translate --sync` を呼ぶか `translate.sync` を import できます。


### Solve

Ize は run_target('posync') をプロジェクトの Python エントリ経由で translate --sync を呼ぶよう書き換えます（zfr 内では import 優先）。その後 POTFILES と言語フラグを確認。
