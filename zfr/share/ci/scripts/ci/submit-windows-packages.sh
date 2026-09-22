#!/usr/bin/env bash
# Generate + optionally submit Windows package manifests:
#   WinGet:  native + mingw (-gnu)
#   Scoop:   native + mingw (-gnu)
#   Choco:   single package bundling native + mingw
#
# Usage: submit-windows-packages.sh <dist-root> <version>
#
# Env (optional submit):
#   WINGET_SUBMIT=1   + GH_TOKEN with fork/PR rights for microsoft/winget-pkgs
#   SCOOP_BUCKET_REPO=owner/scoop-bucket  + GH_TOKEN
#   CHOCO_API_KEY=...  (chocolatey.org push)
#   WINGET_PUBLISHER=Lenik   (WinGet PackageIdentifier prefix)
set -euo pipefail

DIST=${1:?dist-root}
VERSION=${2:?version}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
NAME=$(basename "$ROOT")
PUB=${WINGET_PUBLISHER:-Lenik}
# PackageIdentifier: Lenik.BasC / Lenik.BasC.Gnu
IDENT_NATIVE=$(python3 -c "print('${PUB}.'+''.join(p.capitalize() for p in '${NAME}'.replace('_','-').split('-')))")
IDENT_GNU="${IDENT_NATIVE}.Gnu"
OUT="$DIST/windows-manifests"
mkdir -p "$OUT/winget/native" "$OUT/winget/gnu" "$OUT/scoop" "$OUT/choco/tools"

shopt -s nullglob
NATIVE_ZIPS=("$DIST"/ucrt-*/*.zip "$DIST"/*ucrt*.zip)
GNU_ZIPS=("$DIST"/mingw-*/*.zip "$DIST"/*mingw*.zip)
NATIVE_NUPKGS=("$DIST"/ucrt-*/*.nupkg "$DIST"/${NAME}.${VERSION}.nupkg)
GNU_NUPKGS=("$DIST"/mingw-*/*.nupkg "$DIST"/${NAME}.gnu.${VERSION}.nupkg)

pick() { for f in "$@"; do [ -f "$f" ] && { echo "$f"; return 0; }; done; return 1; }

native_zip=$(pick "${NATIVE_ZIPS[@]}" || true)
gnu_zip=$(pick "${GNU_ZIPS[@]}" || true)
native_nupkg=$(pick "${NATIVE_NUPKGS[@]}" || true)
gnu_nupkg=$(pick "${GNU_NUPKGS[@]}" || true)

sha256() { sha256sum "$1" | awk '{print $1}'; }

# --- Scoop manifests ---
if [ -n "${native_zip:-}" ]; then
  cat >"$OUT/scoop/${NAME}.json" <<EOF
{
  "version": "${VERSION}",
  "description": "${NAME} native Windows (UCRT)",
  "homepage": "https://github.com/lenik/${NAME}",
  "license": "AGPL-3.0-or-later",
  "url": "RELEASE_ASSET:${NAME}-ucrt-x64.zip",
  "hash": "sha256:$(sha256 "$native_zip")",
  "bin": []
}
EOF
  echo "scoop: wrote $OUT/scoop/${NAME}.json"
fi
if [ -n "${gnu_zip:-}" ]; then
  cat >"$OUT/scoop/${NAME}-gnu.json" <<EOF
{
  "version": "${VERSION}",
  "description": "${NAME} MinGW-w64 (-gnu)",
  "homepage": "https://github.com/lenik/${NAME}",
  "license": "AGPL-3.0-or-later",
  "url": "RELEASE_ASSET:${NAME}-mingw-x64.zip",
  "hash": "sha256:$(sha256 "$gnu_zip")",
  "bin": []
}
EOF
  echo "scoop: wrote $OUT/scoop/${NAME}-gnu.json"
fi

# --- WinGet manifests (minimal singleton) ---
winget_yaml() {
  local ident=$1 ver=$2 zip=$3 tag=$4
  local hash
  hash=$(sha256 "$zip")
  cat <<EOF
PackageIdentifier: ${ident}
PackageVersion: ${ver}
PackageLocale: en-US
Publisher: ${PUB}
PackageName: ${NAME}${tag}
License: AGPL-3.0-or-later
ShortDescription: ${NAME} Windows package${tag}
Installers:
  - Architecture: x64
    InstallerType: zip
    InstallerUrl: https://github.com/lenik/${NAME}/releases/download/v${ver}/$(basename "$zip")
    InstallerSha256: ${hash}
ManifestType: singleton
ManifestVersion: 1.6.0
EOF
}

if [ -n "${native_zip:-}" ]; then
  winget_yaml "$IDENT_NATIVE" "$VERSION" "$native_zip" "" \
    >"$OUT/winget/native/${IDENT_NATIVE}.yaml"
  echo "winget: wrote native $IDENT_NATIVE"
fi
if [ -n "${gnu_zip:-}" ]; then
  winget_yaml "$IDENT_GNU" "$VERSION" "$gnu_zip" " (-gnu)" \
    >"$OUT/winget/gnu/${IDENT_GNU}.yaml"
  echo "winget: wrote gnu $IDENT_GNU"
fi

# --- Chocolatey: one package with native + mingw ---
NUSPEC="$OUT/choco/${NAME}.nuspec"
cat >"$NUSPEC" <<EOF
<?xml version="1.0"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>${NAME}</id>
    <version>${VERSION}</version>
    <title>${NAME}</title>
    <authors>${PUB}</authors>
    <description>${NAME} Windows binaries (UCRT native + MinGW -gnu)</description>
    <tags>windows ucrt mingw gnu</tags>
  </metadata>
  <files>
    <file src="tools\\**" target="tools" />
  </files>
</package>
EOF
# stage tools from available zips
if [ -n "${native_zip:-}" ]; then
  mkdir -p "$OUT/choco/tools/native"
  unzip -qo "$native_zip" -d "$OUT/choco/tools/native" || cp -a "$native_zip" "$OUT/choco/tools/"
fi
if [ -n "${gnu_zip:-}" ]; then
  mkdir -p "$OUT/choco/tools/mingw-gnu"
  unzip -qo "$gnu_zip" -d "$OUT/choco/tools/mingw-gnu" || cp -a "$gnu_zip" "$OUT/choco/tools/"
fi
cat >"$OUT/choco/tools/chocolateyInstall.ps1" <<'EOF'
$ErrorActionPreference = 'Stop'
Write-Host "Installed native (tools/native) and mingw-gnu (tools/mingw-gnu)."
EOF

# Pack choco nupkg via zip/nuget layout
python3 "$ROOT/scripts/ci/pack-nuget.py" \
  --id "$NAME" \
  --version "$VERSION" \
  --stage "$OUT/choco/tools" \
  --out "$OUT/choco/${NAME}.${VERSION}.nupkg" \
  --rid win-x64 \
  --description "${NAME} Chocolatey (native + mingw-gnu)" \
  2>/dev/null || {
  # fallback: zip as nupkg-ish
  ( cd "$OUT/choco" && zip -qr "${NAME}.${VERSION}.nupkg" tools "${NAME}.nuspec" )
}
echo "choco: wrote $OUT/choco/${NAME}.${VERSION}.nupkg"

# --- Optional submits ---
if [ "${WINGET_SUBMIT:-0}" = 1 ] && [ -n "${GH_TOKEN:-}" ]; then
  echo "submit-windows: WINGET_SUBMIT requested — use wingetcreate / open PR to microsoft/winget-pkgs with $OUT/winget/"
  # Non-interactive placeholder: upload manifests as release assets; full PR needs wingetcreate.
fi
if [ -n "${SCOOP_BUCKET_REPO:-}" ] && [ -n "${GH_TOKEN:-}" ]; then
  echo "submit-windows: scoop bucket $SCOOP_BUCKET_REPO — copy $OUT/scoop/*.json then gh pr create"
fi
if [ -n "${CHOCO_API_KEY:-}" ]; then
  if command -v choco >/dev/null 2>&1; then
    choco push "$OUT/choco/${NAME}.${VERSION}.nupkg" --source https://push.chocolatey.org/ --api-key "$CHOCO_API_KEY" || true
  else
    echo "submit-windows: choco CLI missing; nupkg ready at $OUT/choco/"
  fi
fi

echo "submit-windows: manifests under $OUT"
