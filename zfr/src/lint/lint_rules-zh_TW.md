## ZL0001

### 長文件不利於歸屬

過長的源文件難以審閱、測試和歸屬。Zephyr 更傾向把內聚模塊放到包目錄下，入口文件保持精簡——create/ize 也按這個形狀工作。


### 改進能帶來什麼

更小的審閱 diff、更清晰的模塊邊界、更容易寫單元測試，以及在熱點文件上更少的合併衝突。


### 閾值

Lint 統計非空行（跳過 build/debian/po/…）。約 600 行給出提示，約 1000 行給出警告。模板示例模塊會被跳過。


### 修復需人工

自行拆分文件並更新 meson/安裝/導入列表。`zfr ize` 不會自動拆分源文件。


## ZL0090
### 硬編碼 /usr 會破壞前綴

絕對 FHS 路徑（/usr/share、/usr/bin 等）在 DESTDIR、非標準前綴以及 Meson configure_file 暫存下會失敗。


### 推薦形態

腳本使用 @PREFIX@ / @DATADIR@ / @LOCALEDIR@（或等價物），並通過 Meson 從 *.in 安裝。


### Solve 做什麼

ize 會把受影響腳本改名為 *.in 並接入 configure_file。請複查 shebang 以及假定了實路徑的測試。


## ZL0091
### 版本字面量會漂移

硬編碼的發佈字符串一旦 bump，就會與 debian/changelog 和 Meson project_version() 分叉。


### 單一事實來源

優先使用構建時替換的 @VERSION@ / PROJECT_VERSION，這樣 `--version`、包裝腳本和軟件包保持一致。


### 轉換時的風險

C/C++ 通常需要 config.h；腳本需要 *.in。大樹請先用 ize 幹跑（`-n`）再寫入。


## ZL0094
### 只有替換沒有消費者是不完整的

Meson 必須既定義 VERSION/PROJECT_VERSION，又有源碼真正讀取它——否則打包出的二進制仍會撒謊。


### 如何檢查

查找 configuration_data 鍵，以及已安裝源碼中的 @VERSION@ / PROJECT_VERSION 用法。


### 閉環

補上缺失的一半（替換或消費者）。可用時 Solve 會映射到 subst 的 ize 步驟。


## ZL0095
### 內聯 posync 難以維護

meson.build 裡的 bash -euc heredoc 會在模板間重複，且難調試。約定是由 run_target('posync') 調用 `zfr translate --sync`（Python），而不是內聯 heredoc。


### 收益

一條命令在本地同步 xgettext/msgmerge；ninja posync 保持簡短；CI 可調用 `zfr translate --sync`，或在 zfr 內 import `translate.sync`。


### Solve

ize 會把 run_target('posync') 改寫為通過項目 Python 入口調用 translate --sync（zfr 內部優先 import）。之後請核對 POTFILES 與語言標誌。


## ZL0096
### 維護腳本應放在 scripts/

倉庫根上的 install-symlinks / deploy 輔助腳本會弄亂打包表面。Zephyr 把它們放在 scripts/。目錄同步與 DESTDIR 預覽優先用 `zfr translate --sync` 與 `zfr build --look`，而不是專用的 posync.sh/look.sh。


### 檢測

標記根目錄維護用 *.sh，以及應外置或改成 zfr 子命令的內聯 run_target 體。


### 搬遷之後

更新文檔以及仍調用舊路徑的 CI。Solve 會把 Meson run_target 改寫到 scripts/… 或 zfr translate/build。


## family:debian

### Debian 是 APT 契約

control / rules / copyright / source format 決定軟件包如何構建以及用戶裝到什麼。Zephyr 統一為 Meson + dh `--buildsystem=meson --builddirectory=debian/build`。


### 本檢查：{title}

{detail}
      默認嚴重級別提示：{sev}。


### 為什麼重要

錯誤的 Architecture、缺失 Build-Depends，或非 Meson 的 rules，即使本地編譯成功也會讓 debuild 失敗或產出無法安裝的包。


### 編輯打包時

ize 可能按模板改寫——上傳前務必 diff Maintainer、Depends 與 Architecture。


## family:rpm

### RPM 必須鏡像 Meson/Debian

spec 的 %files、BuildArch 與 Version 必須描述 Meson 實際安裝的同一批載荷。項目本地 rpmbuild TOPDIR 與過期文件列表是常見故障。


### 本檢查：{title}

{detail}
      嚴重級別提示：{sev}。


### 典型後果

未打包文件、錯誤的 noarch/ELF、殘留 rpmbuild/，或把 Debian substvars 抄進 Requires。


## family:meson

### Meson 是權威構建系統

身份、許可證、版本來源、手冊頁、補全以及 look/posync 目標都在 meson.build。這裡漂移會同時弄壞 Debian 與 RPM。


### 本檢查：{title}

{detail}


### 編輯提示

ize 會補丁 meson.build；大改後請把自定義目標與模板塊對齊並重新 configure。


## family:i18n

### 語言環境是產品表面

Gettext 目錄與整篇 man/<locale>/ 頁面決定用戶在配置的 l10n 級別（`-l` / lint.options）下看到什麼。


### 本檢查：{title}

{detail}


### 仍需人工

ize 可以樁接 .po 並修 wrap 風格；真正的翻譯與手冊本地化仍需人（或 `zfr translate`）。瀏覽用長文放在 lint_rules-<locale>.xml——請手譯；機器翻譯太慢就不要等。


## family:layout

### 共享佈局讓工具有方向

LICENSE、man/、VERSION、hooks、補全與 scripts/ 是 create/ize/lint/release 所依賴的地標。


### 缺失或錯誤：{title}

{detail}


### 腳手架刷新

Solve 可能從模板安裝或刷新文件（.githooks、LICENSE、cursor rules 等）。提交前請審閱。


## family:lang

### 語言模板期望

{title}。每種語言保留慣用標記（tests/、Cargo.toml、bas i18n 輔助、bash *.in 等），以便樹保持可打包。


### 細節

{detail}


## family:identity

### 跨生態一個名字

目錄名、meson project()、debian Source 與 RPM Name 必須一致。不一致會困擾 rename、release 與倉庫。


### 檢查：{title}

{detail}


## family:source

### 源碼衛生

{title}。覆蓋長度以及會破壞可重定位安裝的硬編碼路徑/版本。


### lint 如何看

{detail}


## family:tokens

### {title}

{detail}


## family:template

### {title}

{detail}


## family:readme

### {title}

{detail}


## family:generic

### {title}

規則 {id}（`{code}`）屬於 zephyr 打包/佈局契約。默認嚴重級別提示：{sev}。


### lint 做什麼

{detail}
      在 `zfr lint` 中實現為 `{code}`。發現項儘可能帶具體 fix。可用 `-w` / `-e` / `--strict` 重映射嚴重級別。


### 改動樹時

修復可能觸及打包、meson.build、源碼或腳手架副本。上傳前 diff Maintainer、Depends、%files 與 *.in 腳本。


## ize

### Solve / ize

點擊 Solve 僅運行：{targets}。
      等價 CLI：`{cmd}`
      用 `-n` 做幹跑。輸出經 fdmux 捕獲（有序 stdout/stderr）。


### 無 Solve 映射 {none}

此發現沒有 `zfr ize --only …` 快捷方式。請按 fix 文本處理（或若有多處相關缺口則用更廣的 `zfr ize`），然後重新 lint。
