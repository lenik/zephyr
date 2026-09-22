# Project version substituted by Meson config and used in at least one source

### 只有替換沒有消費者是不完整的

Meson 必須既定義 VERSION/PROJECT_VERSION，又有源碼真正讀取它——否則打包出的二進制仍會撒謊。


### 如何檢查

查找 configuration_data 鍵，以及已安裝源碼中的 @VERSION@ / PROJECT_VERSION 用法。


### 閉環

補上缺失的一半（替換或消費者）。可用時 Solve 會映射到 subst 的 ize 步驟。
