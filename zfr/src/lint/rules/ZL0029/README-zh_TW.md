# packaging/rpm/Makefile clean 刪除整個 TOPDIR

### RPM 須鏡像 Meson/Debian

spec 的 %files、BuildArch 與 Version 必須描述 Meson 安裝的同一載荷。專案本地 rpmbuild TOPDIR 與過期檔案清單是常見失敗模式。


### 本檢查：{title}

{detail}
嚴重程度提示：{sev}。


### 典型後果

未打包檔案、錯誤的 noarch/ELF、殘留 rpmbuild/，或把 Debian substvars 複製進 Requires。
