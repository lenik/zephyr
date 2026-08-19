# zephyr

多语言命令行项目模板与辅助工具。

模板安装在 `/usr/share/zephyr/<lang>/`，通过 `zephyr` 创建工程并管理示例应用（puff）。

## 快速开始

```bash
zephyr create -l python myproj
cd myproj
zephyr add myapp
```

支持语言包括 bash、c、clib、cpp、cpplib、csharp、erlang、go、haskell、java、perl、python、ruby、rust、smalltalk、swift、typescript。详见 [README.md](README.md) 与 `man 1 zephyr`。

`zephyr lint` 按 zephyr 打包风格检查工程（缺文件、Meson/Debian/RPM 用法、残留模板名），并给出可执行的修改建议；终端下用 CSR 着色。`zephyr dist` 生成源码包（git 根目录用 `meson dist`，嵌套语言模板只打包当前工程），供 `rpm/Makefile` 与 `ninja srcdist` 复用。
