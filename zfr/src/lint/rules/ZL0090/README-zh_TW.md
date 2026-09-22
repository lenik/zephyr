# Hardcoded FHS install paths in sources (use @DATADIR@ / configure_file)

### 硬編碼 /usr 會破壞前綴

絕對 FHS 路徑（/usr/share、/usr/bin 等）在 DESTDIR、非標準前綴以及 Meson configure_file 暫存下會失敗。


### 推薦形態

腳本使用 @PREFIX@ / @DATADIR@ / @LOCALEDIR@（或等價物），並通過 Meson 從 *.in 安裝。


### Solve 做什麼

ize 會把受影響腳本改名為 *.in 並接入 configure_file。請複查 shebang 以及假定了實路徑的測試。
