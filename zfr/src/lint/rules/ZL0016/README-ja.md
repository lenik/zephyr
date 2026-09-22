# VERSION が debian/changelog と一致

### 単一の信頼源

`VERSION` は最新の `debian/changelog` 項目と一致すべきです。標準の `.githooks/pre-commit`（`core.hooksPath=.githooks` と併用）がコミット時に `VERSION` を書き直します。


### 同期フックが設定されているとき

その pre-commit フックがあり changelog から VERSION を同期するなら、次のコミットまでの一時的な不一致は想定内——lint は警告ではなく **ok** を報告します。


### フックが無いとき

不一致は **warn**：手で VERSION を揃えるか、`zfr ize` で標準フックを入れ、`git config core.hooksPath .githooks`。
