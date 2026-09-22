# 專案版本由 Meson config 替換且至少在一個原始碼中使用

meson.build 應透過 configuration_data（ize_cfg / config_h / paths_cfg）提供 VERSION/PROJECT_VERSION，且 src/ 下至少一個原始碼（或 configure_file 輸入）必須消費 @VERSION@ 或 PROJECT_VERSION。

### 有替換無消費者是不完整的

Meson 必須既定義 VERSION/PROJECT_VERSION，又有真正讀取它的原始碼——否則打包後的二進位仍會說謊。


### 如何檢查

查找 configuration_data 鍵，以及已安裝原始碼中的 @VERSION@ / PROJECT_VERSION 用法。


### 閉環

補上缺失的一半（替換或消費者）。Solve 在可用時對應到 subst 的 ize 步驟。
