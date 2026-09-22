# scripts/ci 輔助用於多發行版套件建置

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
