# packaging/rpm/*.patch موصول كـ PatchN + %autosetup/%patch

يجب إدراج رقع RPM فقط تحت packaging/rpm/*.patch كـ PatchN: في المواصفة وتطبيقها في %prep (%autosetup -p1 أو %patch -PN -p1). Makefile و build-rpm.sh ينسخانها إلى SOURCES.

### يجب أن يعكس RPM Meson/Debian

يجب أن تصف %files و BuildArch و Version في المواصفة نفس الحمولة التي يثبّتها Meson. TOPDIR لـ rpmbuild محلي للمشروع وقوائم ملفات قديمة أنماط فشل شائعة.


### هذا الفحص: {title}

{detail}
تلميح الشدة: {sev}.


### العواقب النموذجية

ملفات غير معبأة، noarch/ELF خاطئ، rpmbuild/ متبقٍ، أو substvars لديبيان منسوخة إلى Requires.
