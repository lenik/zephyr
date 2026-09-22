# إصدار المشروع يُستبدل بتهيئة Meson ويُستخدم في مصدر واحد على الأقل

يجب أن يغذّي meson.build VERSION/PROJECT_VERSION عبر configuration_data (ize_cfg / config_h / paths_cfg)، ويجب أن يستهلك مصدر واحد على الأقل تحت src/ (أو مدخل configure_file) @VERSION@ أو PROJECT_VERSION.

### الاستبدال بلا مستهلك غير مكتمل

يجب أن يعرّف Meson VERSION/PROJECT_VERSION وأن تكون هناك مصادر تقرأه فعليًا — وإلا تظل الثنائيات المعبأة تكذب.


### كيف يُفحص

يبحث عن مفاتيح configuration_data واستخدام @VERSION@ / PROJECT_VERSION في المصادر المثبتة.


### إغلاق الحلقة

أضف النصف الناقص (استبدال أو مستهلك). يربط Solve بخطوات ize للاستبدال عند التوفر.
