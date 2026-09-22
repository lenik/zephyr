# RPM %files يغطي فهارس gettext .mo

### يجب أن يعكس RPM Meson/Debian

يجب أن تصف %files و BuildArch و Version في المواصفة نفس الحمولة التي يثبّتها Meson. TOPDIR لـ rpmbuild محلي للمشروع وقوائم ملفات قديمة أنماط فشل شائعة.


### هذا الفحص: {title}

{detail}
تلميح الشدة: {sev}.


### العواقب النموذجية

ملفات غير معبأة، noarch/ELF خاطئ، rpmbuild/ متبقٍ، أو substvars لديبيان منسوخة إلى Requires.
