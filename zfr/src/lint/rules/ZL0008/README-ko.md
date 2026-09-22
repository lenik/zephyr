# debian/control의 Build-Depends 항목

### Debian은 APT 계약입니다

control / rules / copyright / source format이 패키지 빌드 방식과 사용자가 설치하는 내용을 결정합니다. Zephyr는 Meson + dh `--buildsystem=meson --builddirectory=debian/build`로 표준화합니다.


### 이 검사: {title}

{detail}
기본 심각도 힌트: {sev}.


### 왜 중요한가

잘못된 Architecture, 누락된 Build-Depends, 또는 비-Meson rules 파일은 debuild를 실패시키거나, 로컬 컴파일이 되어도 로드할 수 없는 패키지를 만듭니다.


### 패키징을 편집할 때

Ize가 템플릿으로 다시 쓸 수 있습니다 — 업로드 전에 항상 Maintainer, Depends, Architecture를 diff하세요.
