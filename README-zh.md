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
