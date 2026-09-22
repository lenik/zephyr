# bash 套件 Depends 包含 bash-shlib

### Debian 是 APT 契約

control / rules / copyright / source format 決定套件如何建置以及使用者安裝到什麼。Zephyr 統一採用 Meson + dh `--buildsystem=meson --builddirectory=debian/build`。


### 本檢查：{title}

{detail}
預設嚴重程度提示：{sev}。


### 為何重要

錯誤的 Architecture、缺少 Build-Depends，或非 Meson 的 rules 檔會導致 debuild 失敗，或產出無法載入的套件——即便本機編譯成功。


### 編輯打包時

Ize 可能依範本重寫——上傳前務必 diff Maintainer、Depends 與 Architecture。
