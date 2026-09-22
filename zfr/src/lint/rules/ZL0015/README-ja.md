# debian/source/format ネイティブ 3.0

### Debian は APT 契約です

コントロール / ルール / 著作権 / ソース形式によって、パッケージの構築方法とユーザーが何をインストールするかが決まります。 Zephyr は Meson + dh `--buildsystem=meson --builddirectory=debian/build` を標準化しています。


### このチェック: {title}

{詳細}
デフォルトの重大度ヒント: {sev}。


### なぜそれが重要なのか

アーキテクチャが間違っている、Build-Depends が欠落している、または非 Meson ルール ファイルがあると、ローカル コンパイルが成功した場合でも、デビルドに失敗するか、アンロード可能なパッケージが生成されます。


### パッケージを編集する場合

Ize はテンプレートから書き直す可能性があります。アップロードする前に、必ず Maintainer、Depends、Architecture を比較してください。
