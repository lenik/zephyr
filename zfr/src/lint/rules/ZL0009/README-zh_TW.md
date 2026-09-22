# Build-Depends 中的 debhelper-compat

### Debian 是 APT 合約

控制/規則/版權/來源格式決定套件如何建置以及使用者安裝什麼。 Zephyr 在 Meson + dh `--buildsystem=meson --builddirectory=debian/build` 上進行標準化。


### 此檢查：{title}

{細節}
預設嚴重性提示：{sev}。


### 為什麼這很重要

錯誤的架構、缺少 Build-Depends 或非 Meson 規則檔案即使本機編譯成功，也無法進行反編譯或產生不可載入的套件。


### 編輯包裝時

Ize 可以從範本重寫 - 在上傳之前始終比較維護者、依賴項和架構。
