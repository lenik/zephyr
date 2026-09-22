# Hardcoded project version in sources (use @VERSION@ / PROJECT_VERSION)

### 版本字面量會漂移

硬編碼的發佈字符串一旦 bump，就會與 debian/changelog 和 Meson project_version() 分叉。


### 單一事實來源

優先使用構建時替換的 @VERSION@ / PROJECT_VERSION，這樣 `--version`、包裝腳本和軟件包保持一致。


### 轉換時的風險

C/C++ 通常需要 config.h；腳本需要 *.in。大樹請先用 ize 幹跑（`-n`）再寫入。
