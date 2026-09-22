# debian/control の Homepage フィールド

### Debian は APT の契約です

control / rules / copyright / source format がパッケージのビルド方法とインストール内容を決めます。Zephyr は Meson + dh `--buildsystem=meson --builddirectory=debian/build` に標準化しています。


### この検査: {title}

{detail}
既定の重大度ヒント: {sev}。


### なぜ重要か

誤った Architecture、欠けた Build-Depends、非 Meson の rules は debuild を失敗させたり、ローカルではビルドできても読み込めないパッケージを生み出します。


### パッケージングを編集するとき

Ize はテンプレートから書き換えることがあります——アップロード前に必ず Maintainer、Depends、Architecture を diff してください。
