# GitHub Actions の release-packages ワークフロー（Docker マトリクス、ネスト依存なし）

release published で起動する .github/workflows/release-packages.yml と scripts/ci ヘルパーを期待します。ピア依存は scripts/ci/deps.conf とインストール専用フェッチ（ネストビルド禁止）。Apt コンポーネントは main。

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
