# CI 矩陣架構策略（debian armhf/v7；raspi armhf/v6；uos/kylin loong64）

Debian armhf 使用 linux/arm/v7；raspi_* 使用 linux/arm/v6。loong64 僅用於 uos_*/kylin_*。Ubuntu 可能增加 i386/amd64v3；另有 mingw/cygwin 矩陣段用於 Windows 原生建置。

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
