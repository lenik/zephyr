# debian/control 存在扩展 Description

### Debian 是 APT 契约

control / rules / copyright / source format 决定软件包如何构建以及用户安装到什么。Zephyr 统一采用 Meson + dh `--buildsystem=meson --builddirectory=debian/build`。


### 本检查：{title}

{detail}
默认严重级别提示：{sev}。


### 为何重要

错误的 Architecture、缺失 Build-Depends，或非 Meson 的 rules 文件会导致 debuild 失败，或生成无法加载的包——即便本地编译成功。


### 编辑打包时

Ize 可能按模板重写——上传前务必 diff Maintainer、Depends 与 Architecture。
