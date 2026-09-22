# packaging/rpm/*.patch 接入为 PatchN + %autosetup/%patch

仅用于 RPM 的补丁 packaging/rpm/*.patch 必须在 spec 中列为 PatchN:，并在 %prep 中应用（%autosetup -p1 或 %patch -PN -p1）。Makefile 与 build-rpm.sh 会把它们复制到 SOURCES。

### RPM 须镜像 Meson/Debian

spec 的 %files、BuildArch 与 Version 必须描述 Meson 安装的同一载荷。项目本地 rpmbuild TOPDIR 与过期文件列表是常见失败模式。


### 本检查：{title}

{detail}
严重级别提示：{sev}。


### 典型后果

未打包文件、错误的 noarch/ELF、残留 rpmbuild/，或把 Debian substvars 复制进 Requires。
