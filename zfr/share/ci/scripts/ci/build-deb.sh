#!/usr/bin/env bash
# Build a Debian binary package inside a distro container (no host tooling).
# Usage: build-deb.sh <image> <platform> <release> <arch> [outdir]
set -euo pipefail

IMAGE=${1:?image}
PLATFORM=${2:?platform}
RELEASE=${3:?release}
ARCH=${4:?arch}
OUTDIR=${5:-"dist/debian-${RELEASE}-${ARCH}"}

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
NAME=$(basename "$ROOT")
if [ -f "$ROOT/debian/control" ]; then
  src=$(sed -n 's/^Source:[[:space:]]*//p' "$ROOT/debian/control" | head -n1 | tr -d '[:space:]')
  [ -n "$src" ] && NAME=$src
fi
STAGE=$(mktemp -d)
_cleanup_stage() {
  # Build runs as root inside Docker; clear root-owned files via a container.
  if [ -d "$STAGE" ]; then
    docker run --rm -v "$STAGE:/work" alpine:3.20 sh -c 'rm -rf /work/*' >/dev/null 2>&1 || true
    rm -rf "$STAGE" 2>/dev/null || true
  fi
}
trap _cleanup_stage EXIT

mkdir -p "$OUTDIR"
OUTDIR=$(cd "$OUTDIR" && pwd)

mkdir -p "$STAGE/zfr"
# Copy the working tree (not git archive) so packaging CI sees local fixes and
# so a dangling subprojects symlink does not break extraction.
tar -C "$ROOT" \
  --exclude='./.git' \
  --exclude='./build' \
  --exclude='./obj-*' \
  --exclude='./debian/build' \
  --exclude='./debian/tmp' \
  --exclude='./debian/*.debhelper*' \
  --exclude='./dist' \
  --exclude='./ci-deps' \
  -cf - . | tar -C "$STAGE/zfr" -xf -
# Monorepo agent rules live at ../.cursor/rules relative to the package;
# stage them so meson install can find them inside the container.
mkdir -p "$STAGE/.cursor/rules"
if [ -d "$ROOT/../.cursor/rules" ]; then
  cp -a "$ROOT/../.cursor/rules/." "$STAGE/.cursor/rules/" || true
fi
for rule in version.mdc author.mdc translations.mdc proxy.mdc; do
  [ -f "$STAGE/.cursor/rules/$rule" ] || printf '# stub for CI packaging\n' >"$STAGE/.cursor/rules/$rule"
done
# Monorepo root READMEs installed via meson from ../README*.md
for doc in README.md README-zh_CN.md; do
  if [ -f "$ROOT/../$doc" ]; then
    cp -a "$ROOT/../$doc" "$STAGE/$doc"
  else
    printf '# stub for CI packaging\n' >"$STAGE/$doc"
  fi
done
# Materialize subprojects when the checkout uses a symlink outside the tree.
if [ -L "$ROOT/subprojects" ]; then
  target=$(readlink -f "$ROOT/subprojects" || true)
  if [ -n "$target" ] && [ -d "$target" ]; then
    rm -rf "$STAGE/zfr/subprojects"
    mkdir -p "$STAGE/zfr/subprojects"
    # Copy only shallow, non-git contents needed for Meson subprojects.
    tar -C "$target" \
      --exclude='./.git' \
      --exclude='./boost' \
      --exclude='./zash' \
      -cf - . | tar -C "$STAGE/zfr/subprojects" -xf - || true
  fi
fi

# Optional: prebuilt dependency packages (CI_DEPS_DIR), e.g. libbas-c*.deb
if [ -n "${CI_DEPS_DIR:-}" ] && [ -d "$CI_DEPS_DIR" ]; then
  mkdir -p "$STAGE/deps"
  cp -a "$CI_DEPS_DIR"/. "$STAGE/deps/" || true
fi

# Rewrite localhost proxies so apt inside the container can reach the host proxy.
_proxy_for_docker() {
  local v=${1:-}
  v=${v//127.0.0.1/host.docker.internal}
  v=${v//localhost/host.docker.internal}
  printf '%s' "$v"
}
HTTP_PROXY_D=$(_proxy_for_docker "${http_proxy:-${HTTP_PROXY:-}}")
HTTPS_PROXY_D=$(_proxy_for_docker "${https_proxy:-${HTTPS_PROXY:-}}")

docker run --rm --platform "$PLATFORM" \
  -v "$STAGE:/work" \
  -w "/work/zfr" \
  --add-host=host.docker.internal:host-gateway \
  -e DEBIAN_FRONTEND=noninteractive \
  -e "http_proxy=${HTTP_PROXY_D}" \
  -e "https_proxy=${HTTPS_PROXY_D}" \
  -e "HTTP_PROXY=${HTTP_PROXY_D}" \
  -e "HTTPS_PROXY=${HTTPS_PROXY_D}" \
  -e no_proxy -e NO_PROXY \
  -e "REPODEB_URL=${REPODEB_URL:-}" \
  -e "REPODEB_SUITE=${REPODEB_SUITE:-$RELEASE}" \
  -e "REPODEB_COMPONENT=${REPODEB_COMPONENT:-main}" \
  -e "BUILD_SUITE=${RELEASE}" \
  -e "BUILD_ARCH=${ARCH}" \
  -e "DEB_BUILD_OPTIONS=nocheck" \
  "$IMAGE" \
  bash -lc '
set -euo pipefail
# CI packaging: skip dh_auto_test (needs private python3-mesondoc / full tree).
export DEB_BUILD_OPTIONS="${DEB_BUILD_OPTIONS:+$DEB_BUILD_OPTIONS }nocheck"
suite=${BUILD_SUITE:-}
# EOL / stale suite apt sources (official mirrors drop or desync Release/pool).
case "$suite" in
  buster|stretch|jessie)
    printf "%s\n" \
      "deb http://archive.debian.org/debian ${suite} main contrib non-free" \
      "deb http://archive.debian.org/debian-security ${suite}/updates main contrib non-free" \
      > /etc/apt/sources.list
    rm -f /etc/apt/sources.list.d/*
    printf "%s\n" "Acquire::Check-Valid-Until \"false\";" \
      > /etc/apt/apt.conf.d/99archive
    ;;
  bullseye)
    # Live debian-security indexes pool files that 404 on every public
    # mirror; pin a consistent snapshot. Image may be newer → allow downgrades.
    snap=20260809T212255Z
    printf "%s\n" \
      "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/${snap}/ bullseye main contrib non-free" \
      "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/${snap}/ bullseye-security main contrib non-free" \
      "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/${snap}/ bullseye-updates main contrib non-free" \
      > /etc/apt/sources.list
    rm -f /etc/apt/sources.list.d/*
    apt-get clean
    rm -rf /var/lib/apt/lists/*
    printf "%s\n" \
      "Acquire::Retries \"5\";" \
      "Acquire::http::Timeout \"60\";" \
      "Acquire::Check-Valid-Until \"false\";" \
      "Acquire::Languages \"none\";" \
      > /etc/apt/apt.conf.d/99ci-retry
    ;;
esac
# loong64 graduated out of debian-ports into official Debian; old images still
# point at ports (which no longer list loong64).
arch_now=$(dpkg --print-architecture 2>/dev/null || true)
if [ "${BUILD_ARCH:-}" = "loong64" ] || [ "$arch_now" = "loong64" ] || \
   [ "$arch_now" = "loongarch64" ]; then
  printf "%s\n" \
    "deb http://deb.debian.org/debian sid main contrib non-free non-free-firmware" \
    > /etc/apt/sources.list
  rm -f /etc/apt/sources.list.d/*
  apt-get clean
  rm -rf /var/lib/apt/lists/*
fi
# Retry apt update+bootstrap; CDN edges sometimes serve stale Indexes → 404.
_apt_extra=()
[ "${BUILD_SUITE:-}" = "bullseye" ] && _apt_extra+=(--allow-downgrades)
_apt_ok=0
for _try in 1 2 3 4 5; do
  apt-get clean
  rm -rf /var/lib/apt/lists/*
  if apt-get update -qq || apt-get update; then
    if apt-get install -y -qq --no-install-recommends --fix-missing \
      "${_apt_extra[@]}" \
      build-essential debhelper devscripts dpkg-dev fakeroot equivs ca-certificates python3; then
      _apt_ok=1
      break
    fi
  fi
  sleep $((_try * 3))
done
[ "$_apt_ok" = 1 ]
# Prefer private apt (repodeb_aptly) for peer Build-Depends — never nested-build.
# Suite comes from the CI matrix release (trixie/bookworm/…), not changelog
# "stable".
if [ -n "${REPODEB_URL:-}" ]; then
  suite=${REPODEB_SUITE:-${BUILD_SUITE:-trixie}}
  component=${REPODEB_COMPONENT:-main}
  echo "deb [trusted=yes] ${REPODEB_URL%/}/ ${suite} ${component}" \
    > /etc/apt/sources.list.d/repodeb.list
  apt-get update -qq || true
fi
# Optional prebuilt dependency debs (never nested-build other projects).
if ls /work/deps/*.deb >/dev/null 2>&1; then
  dpkg -i /work/deps/*.deb || true
  apt-get -y -f install --no-install-recommends --fix-missing || true
fi
# Peer -dev packages often Requires: glib/curl/zlib via .pc but omit -dev Depends.
apt-get install -y -qq --no-install-recommends --fix-missing \
  "${_apt_extra[@]}" \
  libglib2.0-dev libcurl4-openssl-dev zlib1g-dev libicu-dev bash-builtins \
  pkg-config 2>/dev/null || true
# Drop Build-Depends that apt cannot resolve on this suite (e.g. private
# python3-mesondoc when REPODEB_URL is unset). Build still needs meson tools.
if [ -f debian/control ]; then
  if [ -f /work/zfr/scripts/ci/filter-build-depends.py ]; then
    python3 /work/zfr/scripts/ci/filter-build-depends.py debian/control
  fi
  mk-build-deps -i -r -t "apt-get -y --no-install-recommends --fix-missing ${_apt_extra[*]}" \
    || apt-get install -y --no-install-recommends --fix-missing \
         "${_apt_extra[@]}" \
         meson ninja-build python3 asciidoctor gettext debhelper \
    || true
fi
# Bullseye apt meson (0.56) is below project requirement (>=0.61); use pip.
if [ "${BUILD_SUITE:-}" = "bullseye" ]; then
  apt-get install -y -qq --no-install-recommends --fix-missing \
    "${_apt_extra[@]}" python3-pip python3-setuptools ninja-build 2>/dev/null || true
  pip3 install --no-cache-dir "meson>=0.61,<1.5" || \
    python3 -m pip install --no-cache-dir "meson>=0.61,<1.5"
  export PATH="/usr/local/bin:$PATH"
  hash -r 2>/dev/null || true
  meson --version
  # Python 3.9: rewrite runtime PEP604 unions (same helper as RPM EL8/EL9).
  if [ -f /work/zfr/scripts/ci/patch-py39-aliases.py ]; then
    python3 /work/zfr/scripts/ci/patch-py39-aliases.py /work/zfr || true
  fi
fi
# Debian ships bash.pc; many projects expect the bash-builtins module name.
if ! pkg-config --exists bash-builtins 2>/dev/null; then
  pc=$(find /usr -name bash.pc 2>/dev/null | head -n1 || true)
  if [ -n "${pc:-}" ]; then
    mkdir -p /usr/share/pkgconfig
    cp "$pc" /usr/share/pkgconfig/bash-builtins.pc
  fi
fi
# Foreign / ISA-variant arches (e.g. amd64v3 on an amd64 image).
native=$(dpkg --print-architecture 2>/dev/null || true)
target=${BUILD_ARCH:-$native}
# amd64v3 is an ISA profile, not a dpkg arch — build amd64 and rename later.
dpkg_arch=$target
[ "$target" = "amd64v3" ] && dpkg_arch=amd64
if [ -n "$dpkg_arch" ] && [ "$dpkg_arch" != "$native" ]; then
  dpkg --add-architecture "$dpkg_arch" 2>/dev/null || true
  apt-get update -qq || true
  dpkg-buildpackage -us -uc -b -a"$dpkg_arch"
else
  dpkg-buildpackage -us -uc -b
fi
# Changelog says "stable"; aptly must receive the real build suite.
suite=${BUILD_SUITE:-}
if [ -n "$suite" ]; then
  for ch in /work/*.changes; do
    [ -f "$ch" ] || continue
    sed -i "s/^Distribution:.*/Distribution: ${suite}/" "$ch"
  done
fi
'

shopt -s nullglob
copied=0
for f in "$STAGE"/*.{deb,changes,buildinfo,ddeb}; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  # ISA profile cell: rewrite dpkg arch in the filename (amd64 → amd64v3).
  if [ "$ARCH" = "amd64v3" ]; then
    base=${base/_amd64./_amd64v3.}
  fi
  # name_ver_arch.ext → name_ver_release_arch.ext (release selects the cell)
  if [[ "$base" =~ ^(.+)_([^_]+)_([^_]+)\.(deb|changes|buildinfo|ddeb)$ ]]; then
    dest="${BASH_REMATCH[1]}_${BASH_REMATCH[2]}_${RELEASE}_${BASH_REMATCH[3]}.${BASH_REMATCH[4]}"
  else
    dest="${RELEASE}_${base}"
  fi
  cp -a "$f" "$OUTDIR/$dest"
  copied=$((copied + 1))
done

if [ "$copied" -eq 0 ]; then
  echo "build-deb: no packages produced for ${NAME} ${RELEASE}/${ARCH}" >&2
  exit 1
fi

(
  cd "$OUTDIR"
  zip -q -r "${NAME}-debian-${RELEASE}-${ARCH}.zip" ./*.deb ./*.changes ./*.buildinfo ./*.ddeb 2>/dev/null || \
    zip -q -r "${NAME}-debian-${RELEASE}-${ARCH}.zip" ./*
)
echo "build-deb: wrote $copied artifact(s) → $OUTDIR"
