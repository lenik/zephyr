# Build/deploy/maintenance scripts live under scripts/

### 維護腳本應放在 scripts/

倉庫根上的 install-symlinks / deploy 輔助腳本會弄亂打包表面。Zephyr 把它們放在 scripts/。目錄同步與 DESTDIR 預覽優先用 `zfr translate --sync` 與 `zfr build --look`，而不是專用的 posync.sh/look.sh。


### 檢測

標記根目錄維護用 *.sh，以及應外置或改成 zfr 子命令的內聯 run_target 體。


### 搬遷之後

更新文檔以及仍調用舊路徑的 CI。Solve 會把 Meson run_target 改寫到 scripts/… 或 zfr translate/build。
