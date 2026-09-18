## ZL0001

### 长文件不利于归属

过长的源文件难以审阅、测试和归属。Zephyr 更倾向把内聚模块放到包目录下，入口文件保持精简——create/ize 也按这个形状工作。


### 改进能带来什么

更小的审阅 diff、更清晰的模块边界、更容易写单元测试，以及在热点文件上更少的合并冲突。


### 阈值

Lint 统计非空行（跳过 build/debian/po/…）。约 600 行给出提示，约 1000 行给出警告。模板示例模块会被跳过。


### 修复需人工

自行拆分文件并更新 meson/安装/导入列表。`zfr ize` 不会自动拆分源文件。


## ZL0090
### 硬编码 /usr 会破坏前缀

绝对 FHS 路径（/usr/share、/usr/bin 等）在 DESTDIR、非标准前缀以及 Meson configure_file 暂存下会失败。


### 推荐形态

脚本使用 @PREFIX@ / @DATADIR@ / @LOCALEDIR@（或等价物），并通过 Meson 从 *.in 安装。


### Solve 做什么

ize 会把受影响脚本改名为 *.in 并接入 configure_file。请复查 shebang 以及假定了实路径的测试。


## ZL0091
### 版本字面量会漂移

硬编码的发布字符串一旦 bump，就会与 debian/changelog 和 Meson project_version() 分叉。


### 单一事实来源

优先使用构建时替换的 @VERSION@ / PROJECT_VERSION，这样 `--version`、包装脚本和软件包保持一致。


### 转换时的风险

C/C++ 通常需要 config.h；脚本需要 *.in。大树请先用 ize 干跑（`-n`）再写入。


## ZL0094
### 只有替换没有消费者是不完整的

Meson 必须既定义 VERSION/PROJECT_VERSION，又有源码真正读取它——否则打包出的二进制仍会撒谎。


### 如何检查

查找 configuration_data 键，以及已安装源码中的 @VERSION@ / PROJECT_VERSION 用法。


### 闭环

补上缺失的一半（替换或消费者）。可用时 Solve 会映射到 subst 的 ize 步骤。


## ZL0095
### 内联 posync 难以维护

meson.build 里的 bash -euc heredoc 会在模板间重复，且难调试。约定是由 run_target('posync') 调用 `zfr translate --sync`（Python），而不是内联 heredoc。


### 收益

一条命令在本地同步 xgettext/msgmerge；ninja posync 保持简短；CI 可调用 `zfr translate --sync`，或在 zfr 内 import `translate.sync`。


### Solve

ize 会把 run_target('posync') 改写为通过项目 Python 入口调用 translate --sync（zfr 内部优先 import）。之后请核对 POTFILES 与语言标志。


## ZL0096
### 维护脚本应放在 scripts/

仓库根上的 install-symlinks / deploy 辅助脚本会弄乱打包表面。Zephyr 把它们放在 scripts/。目录同步与 DESTDIR 预览优先用 `zfr translate --sync` 与 `zfr build --look`，而不是专用的 posync.sh/look.sh。


### 检测

标记根目录维护用 *.sh，以及应外置或改成 zfr 子命令的内联 run_target 体。


### 搬迁之后

更新文档以及仍调用旧路径的 CI。Solve 会把 Meson run_target 改写到 scripts/… 或 zfr translate/build。


## family:debian

### Debian 是 APT 契约

control / rules / copyright / source format 决定软件包如何构建以及用户装到什么。Zephyr 统一为 Meson + dh `--buildsystem=meson --builddirectory=debian/build`。


### 本检查：{title}

{detail}
      默认严重级别提示：{sev}。


### 为什么重要

错误的 Architecture、缺失 Build-Depends，或非 Meson 的 rules，即使本地编译成功也会让 debuild 失败或产出无法安装的包。


### 编辑打包时

ize 可能按模板改写——上传前务必 diff Maintainer、Depends 与 Architecture。


## family:rpm

### RPM 必须镜像 Meson/Debian

spec 的 %files、BuildArch 与 Version 必须描述 Meson 实际安装的同一批载荷。项目本地 rpmbuild TOPDIR 与过期文件列表是常见故障。


### 本检查：{title}

{detail}
      严重级别提示：{sev}。


### 典型后果

未打包文件、错误的 noarch/ELF、残留 rpmbuild/，或把 Debian substvars 抄进 Requires。


## family:meson

### Meson 是权威构建系统

身份、许可证、版本来源、手册页、补全以及 look/posync 目标都在 meson.build。这里漂移会同时弄坏 Debian 与 RPM。


### 本检查：{title}

{detail}


### 编辑提示

ize 会补丁 meson.build；大改后请把自定义目标与模板块对齐并重新 configure。


## family:i18n

### 语言环境是产品表面

Gettext 目录与整篇 man/<locale>/ 页面决定用户在配置的 l10n 级别（`-l` / lint.options）下看到什么。


### 本检查：{title}

{detail}


### 仍需人工

ize 可以桩接 .po 并修 wrap 风格；真正的翻译与手册本地化仍需人（或 `zfr translate`）。浏览用长文放在 lint_rules-<locale>.xml——请手翻；机器翻译太慢就不要等。


## family:layout

### 共享布局让工具有方向

LICENSE、man/、VERSION、hooks、补全与 scripts/ 是 create/ize/lint/release 所依赖的地标。


### 缺失或错误：{title}

{detail}


### 脚手架刷新

Solve 可能从模板安装或刷新文件（.githooks、LICENSE、cursor rules 等）。提交前请审阅。


## family:lang

### 语言模板期望

{title}。每种语言保留惯用标记（tests/、Cargo.toml、bas i18n 辅助、bash *.in 等），以便树保持可打包。


### 细节

{detail}


## family:identity

### 跨生态一个名字

目录名、meson project()、debian Source 与 RPM Name 必须一致。不一致会困扰 rename、release 与仓库。


### 检查：{title}

{detail}


## family:source

### 源码卫生

{title}。覆盖长度以及会破坏可重定位安装的硬编码路径/版本。


### lint 如何看

{detail}


## family:tokens

### {title}

{detail}


## family:template

### {title}

{detail}


## family:readme

### {title}

{detail}


## family:generic

### {title}

规则 {id}（`{code}`）属于 zephyr 打包/布局契约。默认严重级别提示：{sev}。


### lint 做什么

{detail}
      在 `zfr lint` 中实现为 `{code}`。发现项尽可能带具体 fix。可用 `-w` / `-e` / `--strict` 重映射严重级别。


### 改动树时

修复可能触及打包、meson.build、源码或脚手架副本。上传前 diff Maintainer、Depends、%files 与 *.in 脚本。


## ize

### Solve / ize

点击 Solve 仅运行：{targets}。
      等价 CLI：`{cmd}`
      用 `-n` 做干跑。输出经 fdmux 捕获（有序 stdout/stderr）。


### 无 Solve 映射 {none}

此发现没有 `zfr ize --only …` 快捷方式。请按 fix 文本处理（或若有多处相关缺口则用更广的 `zfr ize`），然后重新 lint。
