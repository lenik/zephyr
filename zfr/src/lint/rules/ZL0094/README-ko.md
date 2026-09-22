# 프로젝트 버전이 Meson config로 치환되고 최소 하나의 소스에서 사용

meson.build는 configuration_data(ize_cfg / config_h / paths_cfg)로 VERSION/PROJECT_VERSION을 공급해야 하며, src/ 아래 최소 하나의 소스(또는 configure_file 입력)가 @VERSION@ 또는 PROJECT_VERSION을 소비해야 합니다.

### 소비자 없는 치환은 불완전합니다

Meson은 VERSION/PROJECT_VERSION을 정의하고 실제로 읽는 소스도 있어야 합니다 — 그렇지 않으면 패키지된 바이너리가 여전히 거짓말합니다.


### 검사 방식

configuration_data 키와 설치된 소스의 @VERSION@ / PROJECT_VERSION 사용을 찾습니다.


### 고리 닫기

빠진 절반(치환 또는 소비자)을 추가하세요. Solve는 가능하면 subst ize 단계로 매핑합니다.
