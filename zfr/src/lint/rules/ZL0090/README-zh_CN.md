# 源中硬编码的 FHS 安装路径（使用 @DATADIR@ / configure_file）

### 硬编码 /usr 破坏前缀

绝对 FHS 路径（/usr/share、/usr/bin 等）在 DESTDIR、非标准前缀以及 Meson configure_file 暂存下会失败。


### 首选形态

脚本使用 @PREFIX@ / @DATADIR@ / @LOCALEDIR@（或等价物），并由 Meson 通过 *.in 安装。


### Solve 做什么

Ize 将受影响脚本重命名为 *.in 并接线 configure_file。请重新检查 shebang 以及假定了实际路径的测试。
