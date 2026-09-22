# 构建/部署/维护脚本位于 scripts/ 下

根级 *.sh 辅助与 look / install-symlinks / uninstall-symlinks / posync / deploy 的 meson run_target 体应放在 scripts/。运行 `zfr ize` 以移动并重新接线。

### 维护脚本属于 scripts/

仓库根的 install-symlinks / deploy 辅助会搅乱打包表面。Zephyr 把它们放在 scripts/。目录同步与 DESTDIR 预览尽量用 `zfr translate --sync` 与 `zfr build --look`，而非定制 posync.sh/look.sh。


### 检测

标记根级维护用 *.sh 名称，以及应外置或改用 zfr 子命令的内联 run_target 体。


### 移动之后

更新文档以及调用旧路径的 CI。Solve 将 Meson run_target 重写到 scripts/… 或 zfr translate/build。
