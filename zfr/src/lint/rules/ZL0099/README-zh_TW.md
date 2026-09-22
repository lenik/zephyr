# GitHub Actions 的 release-packages 工作流程（Docker 矩陣，無巢狀依賴）

期望 .github/workflows/release-packages.yml 在 release published 時觸發，並有 scripts/ci 輔助腳本。對等相依使用 scripts/ci/deps.conf 與僅安裝式拉取（絕不要巢狀建置）。Apt 元件為 main。

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
