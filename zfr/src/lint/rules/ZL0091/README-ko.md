# 소스의 하드코딩 프로젝트 버전 (@VERSION@ / PROJECT_VERSION 사용)

### 버전 리터럴은 어긋납니다

하드코딩된 릴리스 문자열은 bump하는 순간 debian/changelog와 Meson project_version()에서 갈라집니다.


### 단일 진실 공급원

빌드 시 치환되는 @VERSION@ / PROJECT_VERSION을 써서 `--version`, 래퍼, 패키지를 맞추세요.


### 변환 시 위험

C/C++는 보통 config.h가 필요하고, 스크립트는 *.in이 필요합니다. 큰 트리에서는 쓰기 전에 ize 드라이런(`-n`)을 하세요.
