# GitHub Actions release-packages 워크플로 (Docker 매트릭스, 중첩 deps 없음)

.github/workflows/release-packages.yml이 release published에서 트리거되고 scripts/ci 헬퍼가 있기를 기대합니다. 피어 의존성은 scripts/ci/deps.conf와 설치 전용 fetch를 씁니다(중첩 빌드 금지). Apt 컴포넌트는 main입니다.

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
