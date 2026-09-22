# 原始碼中硬編碼的專案版本（使用 @VERSION@ / PROJECT_VERSION）

### 版本字面量會漂移

硬編碼的發行字串會在你一 bump 就與 debian/changelog 和 Meson project_version() 分叉。


### 單一事實來源

優先在建置時用 @VERSION@ / PROJECT_VERSION 替換，使 `--version`、包裝腳本與套件保持一致。


### 轉換時的風險

C/C++ 通常需要 config.h；腳本需要 *.in。大樹寫入前先對 ize 做乾跑（`-n`）。
