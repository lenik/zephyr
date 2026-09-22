#!/usr/bin/env bash
# Build an RPM inside a Rocky/CentOS container (no host tooling, no zfr).
# Usage: build-rpm.sh <image> <platform> <el_release> <arch> [outdir]
#
# Debian Build-Depends → RPM package mapping (experiential):
#   bash-builtins  → bash (ships bash.pc; prefer packaging/rpm/*.patch + %patch
#                    so Meson accepts bash.pc — do not mutate the container .pc)
#   libglib2.0-dev → glib2-devel
#   libcurl4-*-dev → libcurl-devel
#   zlib1g-dev     → zlib-devel
#   libicu-dev     → libicu-devel
#   pkg-config     → pkgconf
#   meson/ninja-build kept as-is (EPEL/CRB or pip)
set -euo pipefail

IMAGE=${1:?image}
PLATFORM=${2:?platform}
EL=${3:?el_release}
ARCH=${4:?arch}
OUTDIR=${5:-"dist/el-${EL}-${ARCH}"}

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
NAME=$(basename "$ROOT")
VERSION=$(head -n1 "$ROOT/VERSION" 2>/dev/null | tr -d '[:space:]' | sed 's/^v//')
VERSION=${VERSION:-0.0.0}
RPM_VERSION=${VERSION//-/_}
SPEC="$ROOT/packaging/rpm/${NAME}.spec"

if [ ! -f "$SPEC" ]; then
  echo "build-rpm: missing $SPEC" >&2
  exit 1
fi

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$OUTDIR"
OUTDIR=$(cd "$OUTDIR" && pwd)

# Source tarball from the working tree (not git archive) so local fixes are included.
mkdir -p "$STAGE/SOURCES" "$STAGE/SPECS" "$STAGE/RPMS" "$STAGE/BUILD" "$STAGE/BUILDROOT" "$STAGE/SRPMS"
tar -C "$ROOT" \
  --exclude='./.git' \
  --exclude='./build' \
  --exclude='./obj-*' \
  --exclude='./debian/build' \
  --exclude='./debian/tmp' \
  --exclude='./dist' \
  --exclude='./ci-deps' \
  --transform "s,^\\./,${NAME}-${VERSION}/," \
  -cJf "$STAGE/SOURCES/${NAME}-${VERSION}.tar.xz" .

# RPM-only patches: live in packaging/rpm/*.patch; applied via %patch/%autosetup.
shopt -s nullglob
for p in "$ROOT"/packaging/rpm/*.patch; do
  cp -a "$p" "$STAGE/SOURCES/"
done
shopt -u nullglob

{
  printf '%s\n' "%global version ${RPM_VERSION}" "%global srcversion ${VERSION}" ""
  cat "$SPEC"
} >"$STAGE/SPECS/${NAME}.spec"

# Export debian Build-Depends names for in-container mapping (optional).
if [ -f "$ROOT/debian/control" ]; then
  python3 - "$ROOT/debian/control" "$STAGE/debian-build-deps.txt" <<'PY'
import re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
# First stanza Build-Depends (folded)
m = re.search(r"(?ms)^Build-Depends:\s*(.*?)(?=\n\S|\Z)", text)
deps = []
if m:
    raw = re.sub(r"\s*\n\s*", " ", m.group(1))
    for part in raw.split(","):
        name = re.split(r"[(\s|]", part.strip(), 1)[0].strip()
        if name and name not in deps:
            deps.append(name)
Path(sys.argv[2]).write_text("\n".join(deps) + ("\n" if deps else ""), encoding="utf-8")
PY
fi

if [ -n "${CI_DEPS_DIR:-}" ] && [ -d "$CI_DEPS_DIR" ]; then
  mkdir -p "$STAGE/deps"
  cp -a "$CI_DEPS_DIR"/. "$STAGE/deps/" || true
fi

docker run --rm --platform "$PLATFORM" \
  -v "$STAGE:/rpmbuild" \
  -e NAME="$NAME" \
  -e EL="$EL" \
  -e http_proxy -e https_proxy -e HTTP_PROXY -e HTTPS_PROXY \
  -e no_proxy -e NO_PROXY \
  "$IMAGE" \
  bash -lc '
set -euo pipefail
if command -v dnf >/dev/null 2>&1; then
  PM=dnf
elif command -v yum >/dev/null 2>&1; then
  PM=yum
else
  echo "no dnf/yum" >&2; exit 1
fi
# CentOS 7 vault (mirrors are EOL).
if [[ "${EL}" == "7" ]] && [[ -f /etc/yum.repos.d/CentOS-Base.repo ]]; then
  sed -i \
    -e "s|^mirrorlist=|#mirrorlist=|g" \
    -e "s|^#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g" \
    /etc/yum.repos.d/CentOS-*.repo || true
fi
$PM -y install epel-release 2>/dev/null || true
if command -v dnf >/dev/null 2>&1; then
  $PM -y install dnf-plugins-core 2>/dev/null || true
  $PM config-manager --set-enabled crb 2>/dev/null || \
    $PM config-manager --set-enabled powertools 2>/dev/null || true
fi
$PM -y install rpm-build rpmdevtools pkgconf gcc gcc-c++ make \
  tar xz which python3 python3-pip \
  openssl-devel zlib-devel bash || true
# meson/ninja: distro packages (EPEL/CRB) or pip fallback.
$PM -y install meson ninja-build 2>/dev/null \
  || pip3 install --no-cache-dir meson ninja

# Map Debian Build-Depends → RPM packages (experiential heuristics).
map_deb_to_rpm() {
  case "$1" in
    bash-builtins) echo bash ;;  # provides bash.pc; RPM-only %patch teaches Meson
    libglib2.0-dev|libglib2.0-0) echo glib2-devel ;;
    libcurl4-openssl-dev|libcurl4-gnutls-dev|libcurl4-nss-dev|libcurl-dev)
      echo libcurl-devel ;;
    zlib1g-dev|zlib-dev) echo zlib-devel ;;
    libicu-dev) echo libicu-devel ;;
    libssl-dev|openssl) echo openssl-devel ;;
    pkg-config|pkgconf) echo pkgconf ;;
    meson) echo meson ;;
    ninja-build) echo ninja-build ;;
    gettext|gettext-base) echo gettext ;;
    asciidoctor|ruby-asciidoctor) echo asciidoctor ;;
    # packaging-only / skip
    debhelper|debhelper-compat|dh-*|build-essential|fakeroot|equivs|dpkg-dev|devscripts) ;;
    *) ;;
  esac
}

RPM_EXTRA=()
if [[ -f /rpmbuild/debian-build-deps.txt ]]; then
  while read -r debdep || [[ -n "${debdep:-}" ]]; do
    [[ -z "$debdep" ]] && continue
    mapped=$(map_deb_to_rpm "$debdep" || true)
    [[ -n "${mapped:-}" ]] && RPM_EXTRA+=("$mapped")
  done < /rpmbuild/debian-build-deps.txt
fi
# Always pull common C library -devel packages used by bas-c-like projects.
RPM_EXTRA+=(glib2-devel libcurl-devel libicu-devel gettext asciidoctor bash)
# Unique
mapfile -t RPM_EXTRA < <(printf "%s\n" "${RPM_EXTRA[@]}" | awk "NF && !seen[\$0]++")
$PM -y install "${RPM_EXTRA[@]}" 2>/dev/null || true

# Optional prebuilt dependency rpms (never nested-build other projects).
if ls /rpmbuild/deps/*.rpm >/dev/null 2>&1; then
  $PM -y install /rpmbuild/deps/*.rpm || rpm -Uvh --nodeps /rpmbuild/deps/*.rpm || true
fi
command -v meson >/dev/null
command -v ninja >/dev/null || command -v ninja-build >/dev/null

rpmbuild --define "_topdir /rpmbuild" -bb /rpmbuild/SPECS/${NAME}.spec || \
  rpmbuild --define "_topdir /rpmbuild" --nodeps -bb /rpmbuild/SPECS/${NAME}.spec
'

shopt -s nullglob
copied=0
for f in "$STAGE"/RPMS/*/*.rpm "$STAGE"/SRPMS/*.rpm; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  dest="el${EL}_${base}"
  cp -a "$f" "$OUTDIR/$dest"
  copied=$((copied + 1))
done

if [ "$copied" -eq 0 ]; then
  echo "build-rpm: no packages produced for ${NAME} el${EL}/${ARCH}" >&2
  exit 1
fi

(
  cd "$OUTDIR"
  zip -q -r "${NAME}-el-${EL}-${ARCH}.zip" ./*.rpm
)
echo "build-rpm: wrote $copied artifact(s) → $OUTDIR"
