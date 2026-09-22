# RPM CI 對應 Debian Build-Depends；僅 RPM 的修補透過 %patch

當把 debian/control 的 Build-Depends 轉成 rpmbuild 時，按經驗對應：bash-builtins → bash（提供 bash.pc）。僅 RPM 的原始碼調整放在 packaging/rpm/*.patch，用 PatchN + %autosetup/%patch 套用（build-rpm 複製到 SOURCES）；不要在容器裡改動系統 .pc 檔。

### {title}

規則 {id}（`{code}`）屬於 zephyr packaging/
版面配置約定。預設嚴重程度提示：{sev}。

### lint 做什麼

{detail}
在 `zfr lint` 中由 `{code}` 實作。盡可能附帶
具體修復說明。可用 `-w` / `-e` / `--strict` 重對應嚴重程度。

### 變更樹時

修復可能觸及 packaging、meson.build、原始碼或鷹架
副本。上傳前請 diff Maintainer、Depends、%files 與 *.in 腳本。
