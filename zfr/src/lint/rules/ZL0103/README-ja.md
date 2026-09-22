# packaging/rpm/*.patch を PatchN + %autosetup/%patch として配線

RPM 専用パッチ packaging/rpm/*.patch は spec で PatchN: として列挙し、%prep で適用します（%autosetup -p1 または %patch -PN -p1）。Makefile と build-rpm.sh が SOURCES へコピーします。

### RPM は Meson/Debian を鏡写しにする

spec の %files、BuildArch、Version は Meson がインストールする同一ペイロードを記述する必要があります。プロジェクトローカルの rpmbuild TOPDIR と古いファイル一覧はよくある失敗パターンです。


### この検査: {title}

{detail}
重大度ヒント: {sev}。


### 典型的な余波

未パッケージファイル、誤った noarch/ELF、残った rpmbuild/、または Debian substvars が Requires にコピーされること。
