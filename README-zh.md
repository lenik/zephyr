# zephyr

多语言命令行项目模板与辅助工具。

`zfr` 将语言模板安装到 `/usr/share/zephyr/<lang>/`，并提供命令行工具，
用于创建工程和管理示例应用（**puff**）。实例化后的工程应继续在 PATH 上使用
**`zfr`**（如 `zfr version`、`zfr lint`）。工具名 **`zfr` 不是**
create/rename 的魔法替换词；会被改写的占位符仍是 **`zephyr`**
（示例 puff 为 **`some_puff1`**）。

## 安装

### 从源码（Meson）

```bash
sudo apt install meson ninja-build python3 asciidoctor
meson setup /build
ninja -C /build
sudo ninja -C /build install
```

### Debian 包

用常规的 `dpkg-buildpackage` / `debuild` 从源码树构建并安装。运行时依赖
`python3`；建议同时安装 bash 补全。

## 布局

| 路径 | 用途 |
|------|------|
| `/usr/share/zephyr/<lang>/` | 语言模板目录 |
| `/usr/bin/zfr` | 主命令（`create`、`rename`、`add`、`remove`、`about`、`version`、`lint`、`dist`、`ize`、`detect`） |
| `/usr/bin/zfr-{create,rename,add,remove,about,version,lint,dist,ize}` | 薄封装 |
| `man 1 zfr` | 手册页 |

支持的语言包括：**bash**、**c**、**clib**、**cpp**、**cpplib**、**csharp**、**erlang**、
**go**、**haskell**、**java**、**perl**、**python**、**ruby**、**rust**、**smalltalk**、
**swift**、**typescript**。

## 快速开始

```bash
zfr create -l python myproj
cd myproj
zfr add myapp
```

`create` 把模板复制到 `./myproj/`，将工程名从 `zephyr` 改成 `myproj`，默认
去掉示例 puff `some_puff1`。同时写入 `debian/changelog`，并用默认值
`-D unstable`、`-1 0.0.1`、`-a 'Lenik (谢继雷)'`、`-e lenik@bodz.net`
做初次 git 提交与打标签（可用这些选项覆盖）。在 create 命令行上直接给出
puff 名称即可立刻添加：

```bash
zfr create -l c widgets hello world
```

之后用 `zfr add` / `zfr remove` 继续增删 puff（可一次多个名字）。
`zfr lint` 按 zephyr 打包风格检查工程（缺文件、Meson/Debian/RPM 用法、
残留模板名），并给出可执行的修改建议；终端下着色。`zfr dist` 生成源码包
（git 根目录用 `meson dist`，否则只打包当前工程），供 `rpm/Makefile` 与
`ninja srcdist` 复用。`zfr ize` 把已有工程升级到当前 zephyr 风格（补
debian/rpm、Meson 目标、AsciiDoc 手册、Meson 版本替换）。

## 测试

父仓库提供 `tests/`（不安装）。在源码根目录：

```bash
meson setup /build
meson test -C /build
```

Meson 对 `tests/test_*.py` 执行 `python3 -m unittest discover`。测试套件会
建立临时示例工程，并覆盖 CLI（`create`、`add`、`remove`、`rename`、`about`、
`version`、`lint`、`dist`、`ize`、`detect`）。不经 Meson 直接跑时，把
`ZFR_PKGDATADIR` 设为源码根目录，把 `PYTHONPATH` 设为 `tools/`。

## 另见

- `man 1 zfr`
- 各语言模板目录内的 `README.md`
- 英文说明：[README.md](README.md)
