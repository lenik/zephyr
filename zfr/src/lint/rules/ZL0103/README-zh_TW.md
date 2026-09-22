# packaging/rpm/*.patch 接線為 PatchN + %autosetup/%patch

僅用於 RPM 的修補 packaging/rpm/*.patch 必須在 spec 中列為 PatchN:，並在 %prep 中套用（%autosetup -p1 或 %patch -PN -p1）。Makefile 與 build-rpm.sh 會把它們複製到 SOURCES。

### RPM 須鏡像 Meson/Debian

spec 的 %files、BuildArch 與 Version 必須描述 Meson 安裝的同一載荷。專案本地 rpmbuild TOPDIR 與過期檔案清單是常見失敗模式。


### 本檢查：{title}

{detail}
嚴重程度提示：{sev}。


### 典型後果

未打包檔案、錯誤的 noarch/ELF、殘留 rpmbuild/，或把 Debian substvars 複製進 Requires。
