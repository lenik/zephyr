# ソース内のハードコードプロジェクトバージョン（@VERSION@ / PROJECT_VERSION を使用）

### バージョン文字列はずれる

ハードコードしたリリース文字列は、バンプした瞬間に debian/changelog と Meson project_version() から乖離します。


### 単一の信頼源

ビルド時に置換される @VERSION@ / PROJECT_VERSION を使い、`--version`・ラッパー・パッケージを揃えましょう。


### 変換時のリスク

C/C++ は通常 config.h が必要；スクリプトは *.in が必要。大きなツリーでは書き込み前に ize のドライラン（`-n`）を。
