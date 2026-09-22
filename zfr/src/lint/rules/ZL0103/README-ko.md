# packaging/rpm/*.patch가 PatchN + %autosetup/%patch로 연결

RPM 전용 패치 packaging/rpm/*.patch는 spec에 PatchN:으로 나열하고 %prep에서 적용해야 합니다(%autosetup -p1 또는 %patch -PN -p1). Makefile과 build-rpm.sh가 SOURCES로 복사합니다.

### RPM은 Meson/Debian을 미러링해야 합니다

spec의 %files, BuildArch, Version은 Meson이 설치하는 동일 페이로드를 기술해야 합니다. 프로젝트 로컬 rpmbuild TOPDIR과 오래된 파일 목록이 흔한 실패 모드입니다.


### 이 검사: {title}

{detail}
심각도 힌트: {sev}.


### 전형적인 여파

미패키지 파일, 잘못된 noarch/ELF, 남은 rpmbuild/, 또는 Requires에 복사된 Debian substvars.
