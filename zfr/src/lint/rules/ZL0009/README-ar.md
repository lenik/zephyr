# debhelper-compat في Build-Depends

### Debian هو عقد APT

تحدد control / rules / copyright / source format كيف يُبنى الحزمة وما الذي يثبّته المستخدمون. يوحّد Zephyr على Meson + dh `--buildsystem=meson --builddirectory=debian/build`.


### هذا الفحص: {title}

{detail}
تلميح الشدة الافتراضي: {sev}.


### لماذا يهم

Architecture خاطئة أو Build-Depends ناقصة أو ملف rules غير Meson تفشل debuild أو تنتج حزمًا غير قابلة للتحميل حتى إن نجح التجميع المحلي.


### عند تحرير التعبئة

قد يعيد Ize الكتابة من القوالب — قارن دائمًا Maintainer و Depends و Architecture قبل الرفع.
