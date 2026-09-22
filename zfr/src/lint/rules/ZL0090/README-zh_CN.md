# Hardcoded FHS install paths in sources (use @DATADIR@ / configure_file)

### 硬编码 /usr 会破坏前缀

绝对 FHS 路径（/usr/share、/usr/bin 等）在 DESTDIR、非标准前缀以及 Meson configure_file 暂存下会失败。


### 推荐形态

脚本使用 @PREFIX@ / @DATADIR@ / @LOCALEDIR@（或等价物），并通过 Meson 从 *.in 安装。


### Solve 做什么

ize 会把受影响脚本改名为 *.in 并接入 configure_file。请复查 shebang 以及假定了实路径的测试。
