# مسارات تثبيت FHS مضمّنة في المصادر (استخدم @DATADIR@ / configure_file)

### /usr المكتوب حرفيًا يكسر البادئات

مسارات FHS المطلقة (/usr/share و /usr/bin، …) تفشل تحت DESTDIR والبادئات غير القياسية وتجهيز Meson configure_file.


### الشكل المفضّل

تستخدم السكربتات @PREFIX@ / @DATADIR@ / @LOCALEDIR@ (أو ما يعادلها) وتُثبَّت من *.in عبر Meson.


### ماذا يفعل Solve

Ize يعيد تسمية السكربتات المتأثرة إلى *.in ويوصّل configure_file. أعد فحص shebang وأي اختبارات افترضت مسارات حية.
