# プロジェクトバージョンが Meson config で置換され、少なくとも 1 つのソースで使用

meson.build は configuration_data（ize_cfg / config_h / paths_cfg）経由で VERSION/PROJECT_VERSION を供給し、src/ 配下の少なくとも一つのソース（または configure_file 入力）が @VERSION@ または PROJECT_VERSION を消費する必要があります。

### 置換だけで消費者が無いのは不完全

Meson は VERSION/PROJECT_VERSION を定義し、実際に読むソースも持たねばなりません——さもなくばパッケージ済みバイナリは嘘をつきます。


### 検査方法

configuration_data のキーと、インストールされるソース内の @VERSION@ / PROJECT_VERSION 使用を探します。


### ループを閉じる

欠けている半分（置換または消費者）を追加。Solve は可能なとき subst の ize 手順に対応付けます。
