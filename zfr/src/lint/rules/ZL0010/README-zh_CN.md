# debian/control 架构字段

### Debian 是 APT 合约

控制/规则/版权/源格式决定包如何构建以及用户安装什么。 Zephyr 在 Meson + dh `--buildsystem=meson --builddirectory=debian/build` 上进行标准化。


### 此检查：{title}

{细节}
默认严重性提示：{sev}。


### 为什么这很重要

错误的架构、缺少 Build-Depends 或非 Meson 规则文件即使本地编译成功，也无法进行反编译或生成不可加载的包。


### 编辑包装时

Ize 可以从模板重写 - 在上传之前始终比较维护者、依赖项和架构。
