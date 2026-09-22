# 项目版本由 Meson config 替换且至少在一个源中使用

meson.build 应通过 configuration_data（ize_cfg / config_h / paths_cfg）提供 VERSION/PROJECT_VERSION，且 src/ 下至少一个源文件（或 configure_file 输入）必须消费 @VERSION@ 或 PROJECT_VERSION。

### 有替换无无消费者是不完整的

Meson 必须既定义 VERSION/PROJECT_VERSION，又有真正读取它的源——否则打包后的二进制仍会说谎。


### 如何检查

查找 configuration_data 键，以及已安装源中的 @VERSION@ / PROJECT_VERSION 用法。


### 闭环

补上缺失的一半（替换或消费者）。Solve 在可用时映射到 subst 的 ize 步骤。
