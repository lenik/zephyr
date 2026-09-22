# ソース内のハードコード FHS インストールパス（@DATADIR@ / configure_file を使用）

### ハードコードした /usr は接頭辞を壊す

絶対 FHS パス（/usr/share、/usr/bin など）は DESTDIR、非標準接頭辞、Meson configure_file のステージングで失敗します。


### 望ましい形

スクリプトは @PREFIX@ / @DATADIR@ / @LOCALEDIR@（または同等）を使い、Meson 経由で *.in からインストールします。


### Solve の動作

Ize は該当スクリプトを *.in に改名し configure_file を配線します。shebang と実パス前提のテストを再確認してください。
