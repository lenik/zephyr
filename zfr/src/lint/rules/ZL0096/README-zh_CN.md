# Build/deploy/maintenance scripts live under scripts/

### 维护脚本应放在 scripts/

仓库根上的 install-symlinks / deploy 辅助脚本会弄乱打包表面。Zephyr 把它们放在 scripts/。目录同步与 DESTDIR 预览优先用 `zfr translate --sync` 与 `zfr build --look`，而不是专用的 posync.sh/look.sh。


### 检测

标记根目录维护用 *.sh，以及应外置或改成 zfr 子命令的内联 run_target 体。


### 搬迁之后

更新文档以及仍调用旧路径的 CI。Solve 会把 Meson run_target 改写到 scripts/… 或 zfr translate/build。
