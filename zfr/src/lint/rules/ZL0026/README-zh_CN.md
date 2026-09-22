# 可选的 packaging/rpm/*.spec（与 debian/ 并列）

### RPM 须镜像 Meson/Debian

spec 的 %files、BuildArch 与 Version 必须描述 Meson 安装的同一载荷。项目本地 rpmbuild TOPDIR 与过期文件列表是常见失败模式。


### 本检查：{title}

{detail}
严重级别提示：{sev}。


### 典型后果

未打包文件、错误的 noarch/ELF、残留 rpmbuild/，或把 Debian substvars 复制进 Requires。
