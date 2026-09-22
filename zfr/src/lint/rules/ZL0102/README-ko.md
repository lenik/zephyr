# RPM CI가 Debian Build-Depends 매핑; RPM 전용 패치는 %patch

debian/control의 Build-Depends를 rpmbuild로 옮길 때 경험적 매핑을 적용하세요: bash-builtins → bash(bash.pc 제공). RPM 전용 소스 조정은 packaging/rpm/*.patch에 두고 PatchN + %autosetup/%patch로 적용합니다(build-rpm이 SOURCES로 복사); 컨테이너에서 시스템 .pc 파일을 바꾸지 마세요.

### {title}

규칙 {id}(`{code}`)는 zephyr packaging/
레이아웃 계약의 일부입니다. 기본 심각도 힌트: {sev}.

### lint가 하는 일

{detail}
`zfr lint`의 `{code}` 아래에서 구현됩니다. 가능하면
구체적인 수정 문자열을 붙입니다. 심각도는 `-w` / `-e` / `--strict`로 다시 매핑합니다.

### 트리를 바꿀 때

수정은 packaging, meson.build, 소스 또는 스캐폴드
사본에 영향을 줄 수 있습니다. 업로드 전에 Maintainer, Depends, %files, *.in 스크립트를 diff하세요.
