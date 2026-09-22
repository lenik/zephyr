# RPM CI が Debian Build-Depends をマップ；RPM 専用パッチは %patch

debian/control の Build-Depends を rpmbuild に写すときは経験的マッピングを適用：bash-builtins → bash（bash.pc を同梱）。RPM 専用のソース調整は packaging/rpm/*.patch に置き、PatchN + %autosetup/%patch で適用（build-rpm が SOURCES へコピー）；コンテナ内でシステムの .pc を書き換えない。

### {title}

ルール {id}（`{code}`）は zephyr packaging/
レイアウト契約の一部です。既定の重大度ヒント: {sev}。

### lint の動作

{detail}
`zfr lint` 内の `{code}` で実装されています。可能なら
具体的な修正文を付けます。重大度は `-w` / `-e` / `--strict` で再割当てできます。

### ツリーを変えるとき

修正は packaging、meson.build、ソース、スキャフォールド
コピーに触れることがあります。アップロード前に Maintainer、Depends、%files、*.in スクリプトを diff してください。
