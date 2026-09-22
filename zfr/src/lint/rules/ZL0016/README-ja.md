# VERSION が debian/changelog と一致する

### 単一の情報源

`VERSION` は最新の `debian/changelog` エントリと一致する必要があります。標準の `.githooks/pre-commit`（`core.hooksPath=.githooks`）はコミット時に changelog から `VERSION` を書き直します。


### 同期フックが設定されている場合

その pre-commit フックがあり changelog から VERSION を同期するなら、次のコミットまでの一時的な不一致は想定内です——lint は警告ではなく **ok** を報告します。


### フックがない場合

不一致は **warn** です。手で VERSION を揃えるか、`zfr ize` で標準フックを入れ、`git config core.hooksPath .githooks` を実行してください。
