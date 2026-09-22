# 原始碼中硬編碼的 FHS 安裝路徑（使用 @DATADIR@ / configure_file）

### 硬編碼 /usr 破壞前綴

絕對 FHS 路徑（/usr/share、/usr/bin 等）在 DESTDIR、非標準前綴以及 Meson configure_file 暫存下會失敗。


### 首選形態

腳本使用 @PREFIX@ / @DATADIR@ / @LOCALEDIR@（或等價物），並由 Meson 透過 *.in 安裝。


### Solve 做什麼

Ize 將受影響腳本重新命名為 *.in 並接線 configure_file。請重新檢查 shebang 以及假定了實際路徑的測試。
