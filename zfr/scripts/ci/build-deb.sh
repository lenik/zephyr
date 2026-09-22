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

mkdir -p "$STAGE/src"
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
  -cf - . | tar -C "$STAGE/src" -xf -
# Materialize subprojects when the checkout uses a symlink outside the tree.
if [ -L "$ROOT/subprojects" ]; then
  target=$(readlink -f "$ROOT/subprojects" || true)
  if [ -n "$target" ] && [ -d "$target" ]; then
    rm -rf "$STAGE/src/subprojects"
    mkdir -p "$STAGE/src/subprojects"
    # Copy only shallow, non-git contents needed for Meson subprojects.
    tar -C "$target" \
      --exclude='./.git' \
      --exclude='./boost' \
      --exclude='./zash' \
      -cf - . | tar -C "$STAGE/src/subprojects" -xf - || true
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
  -w "/work/src" \
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
  "$IMAGE" \
  bash -lc '
set -euo pipefail
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
    # Image often still lists bullseye/updates with superseded pool filenames.
    printf "%s\n" \
      "deb http://deb.debian.org/debian bullseye main contrib non-free" \
      "deb http://deb.debian.org/debian-security bullseye-security main contrib non-free" \
      "deb http://deb.debian.org/debian bullseye-updates main contrib non-free" \
      > /etc/apt/sources.list
    rm -f /etc/apt/sources.list.d/*
    apt-get clean
    rm -rf /var/lib/apt/lists/*
    ;;
esac
apt-get update -qq
apt-get install -y -qq --no-install-recommends --fix-missing \
  build-essential debhelper devscripts dpkg-dev fakeroot equivs ca-certificates
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
  libglib2.0-dev libcurl4-openssl-dev zlib1g-dev libicu-dev bash-builtins \
  pkg-config 2>/dev/null || true
if [ -f debian/control ]; then
  mk-build-deps -i -r -t "apt-get -y -qq --no-install-recommends --fix-missing"
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
if [ -n "$target" ] && [ "$target" != "$native" ]; then
  dpkg --add-architecture "$target" 2>/dev/null || true
  apt-get update -qq || true
  dpkg-buildpackage -us -uc -b -a"$target"
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
