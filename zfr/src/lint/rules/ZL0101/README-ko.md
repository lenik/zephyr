# CI 매트릭스 arch 정책 (debian armhf/v7; raspi armhf/v6; uos/kylin loong64)

Debian armhf는 linux/arm/v7을 쓰고; raspi_*는 linux/arm/v6을 씁니다. loong64는 uos_*/kylin_*만. Ubuntu는 i386/amd64v3를 추가할 수 있고; Windows 네이티브 빌드용 mingw/cygwin 매트릭스 섹션도 있습니다.

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
