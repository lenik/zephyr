# 源中硬编码的项目版本（使用 @VERSION@ / PROJECT_VERSION）

### 版本字面量会漂移

硬编码的发行字符串会在你一 bump 就与 debian/changelog 和 Meson project_version() 分叉。


### 单一事实来源

优先在构建时用 @VERSION@ / PROJECT_VERSION 替换，使 `--version`、包装脚本与软件包保持一致。


### 转换时的风险

C/C++ 通常需要 config.h；脚本需要 *.in。大树写入前先对 ize 做干跑（`-n`）。
