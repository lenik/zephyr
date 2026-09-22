# 建置/部署/維護腳本位於 scripts/ 下

根級 *.sh 輔助與 look / install-symlinks / uninstall-symlinks / posync / deploy 的 meson run_target 體應放在 scripts/。執行 `zfr ize` 以移動並重新接線。

### 維護腳本屬於 scripts/

倉庫根的 install-symlinks / deploy 輔助會攪亂打包表面。Zephyr 把它們放在 scripts/。目錄同步與 DESTDIR 預覽盡量用 `zfr translate --sync` 與 `zfr build --look`，而非自訂 posync.sh/look.sh。


### 偵測

標記根級維護用 *.sh 名稱，以及應外置或改用 zfr 子命令的內聯 run_target 體。


### 移動之後

更新文件以及呼叫舊路徑的 CI。Solve 將 Meson run_target 重寫到 scripts/… 或 zfr translate/build。
