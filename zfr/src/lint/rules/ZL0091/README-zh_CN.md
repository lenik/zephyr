# Hardcoded project version in sources (use @VERSION@ / PROJECT_VERSION)

### 版本字面量会漂移

硬编码的发布字符串一旦 bump，就会与 debian/changelog 和 Meson project_version() 分叉。


### 单一事实来源

优先使用构建时替换的 @VERSION@ / PROJECT_VERSION，这样 `--version`、包装脚本和软件包保持一致。


### 转换时的风险

C/C++ 通常需要 config.h；脚本需要 *.in。大树请先用 ize 干跑（`-n`）再写入。
