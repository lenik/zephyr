# Build/deploy/maintenance scripts live under scripts/

### سكربتات الصيانة تحت scripts/

install-symlinks/deploy في جذر المستودع تشوّش سطح التحزيم. المزامنة ومعاينة DESTDIR: `zfr translate --sync` و`zfr build --look`.


### الاكتشاف

يعلّم *.sh في الجذر وأجسام run_target المضمّنة التي يجب إخراجها أو استبدالها بأوامر zfr الفرعية.


### بعد النقل

حدّث الوثائق وCI. يعيد Solve كتابة Meson إلى scripts/… أو zfr.
