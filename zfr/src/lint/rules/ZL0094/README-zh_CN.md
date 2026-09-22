# Project version substituted by Meson config and used in at least one source

### 只有替换没有消费者是不完整的

Meson 必须既定义 VERSION/PROJECT_VERSION，又有源码真正读取它——否则打包出的二进制仍会撒谎。


### 如何检查

查找 configuration_data 键，以及已安装源码中的 @VERSION@ / PROJECT_VERSION 用法。


### 闭环

补上缺失的一半（替换或消费者）。可用时 Solve 会映射到 subst 的 ize 步骤。
