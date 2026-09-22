# CI マトリクス arch 方針（debian armhf/v7；raspi armhf/v6；uos/kylin loong64）

Debian armhf は linux/arm/v7；raspi_* は linux/arm/v6。loong64 は uos_*/kylin_* のみ。Ubuntu は i386/amd64v3 を足すことがあり、Windows ネイティブ向けに mingw/cygwin 行列セクションもあります。

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
