#!/usr/bin/env bash
# Publish built packages to private repos
# (repodeb_aptly / reporpm_createrepo-c / reponupkg_forgejo).
#
# Preferred (CI / anonymous):
#   REPODEB_URL=http://host:1130   — PUT /upload/<suite>/ + GET /process?sync=1
#   REPORPM_URL=http://host:1993   — PUT /upload/ + GET /rescan?sync=1
#   REPORPM_USER / REPORPM_PASS    — required for reporpm (auth) unless
#                                    REPORPM_ANON=1 and the server allows it
#   REPONUPKG_URL=http://host:2080/api/packages/<owner>/nuget
#                                    — Forgejo NuGet (reponupkg_forgejo)
#   REPONUPKG_TOKEN                — Forgejo PAT (package write)
#   REPONUPKG_OWNER                — Forgejo owner (default: extracted from URL)
#
# Legacy aliases: REPONUGET_URL/REPONUGET_API_KEY → REPONUPKG_*
#
# Deb suite is taken from the artifact name / path (debian-<suite>-<arch>),
# never from debian/changelog Distribution: (projects use "stable").
#
# Fallback (SSH dput, local machines):
#   DPUT_SSH_KEY + S1_HOST → dput -f s1
set -euo pipefail

DIST_ROOT=${1:-dist}
S1_HOST=${S1_HOST:-s1}
REPODEB_URL=${REPODEB_URL:-}
REPORPM_URL=${REPORPM_URL:-${RPM_REPO_URL:-}}
REPORPM_USER=${REPORPM_USER:-${RPM_REPO_USER:-}}
REPORPM_PASS=${REPORPM_PASS:-${RPM_REPO_PASS:-}}
REPONUPKG_URL=${REPONUPKG_URL:-${REPONUGET_URL:-${NUGET_REPO_URL:-}}}
REPONUPKG_TOKEN=${REPONUPKG_TOKEN:-${REPONUGET_API_KEY:-${NUGET_API_KEY:-${FORGEJO_TOKEN:-}}}}
REPONUPKG_OWNER=${REPONUPKG_OWNER:-${FORGEJO_OWNER:-}}

_ARCH_RE='amd64|amd64v3|arm64|armhf|i386|riscv64|loong64|loongarch64|ppc64el|s390x|all'

infer_deb_suite() {
  local hint=$1
  local base suite
  base=$(basename "$hint")
  if [[ "$base" =~ debian-([A-Za-z0-9._+-]+)- ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi
  if [[ "$hint" =~ /debian-([A-Za-z0-9._+-]+)-[^/]+(/|$) ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi
  if [[ "$base" =~ _([A-Za-z0-9._+-]+)_(${_ARCH_RE})\.(deb|changes|buildinfo|ddeb)$ ]]; then
    suite=${BASH_REMATCH[1]}
    case "$suite" in
      stable|unstable|testing|experimental|sid) ;;
      *)
        echo "$suite"
        return 0
        ;;
    esac
  fi
  return 1
}

rewrite_changes_distribution() {
  local dir=$1
  local suite=$2
  local ch
  shopt -s nullglob
  for ch in "$dir"/*.changes; do
    sed -i "s/^Distribution:.*/Distribution: ${suite}/" "$ch"
  done
  shopt -u nullglob
}

normalize_deb_basenames() {
  local dir=$1
  local f base dest
  shopt -s nullglob
  for f in "$dir"/*.{deb,changes,buildinfo,ddeb}; do
    [ -f "$f" ] || continue
    base=$(basename "$f")
    if [[ "$base" =~ ^(.+)_([^_]+)_([A-Za-z0-9._+-]+)_(${_ARCH_RE})\.(deb|changes|buildinfo|ddeb)$ ]]; then
      case "${BASH_REMATCH[3]}" in
        stable|unstable|testing|experimental|sid) continue ;;
      esac
      dest="${BASH_REMATCH[1]}_${BASH_REMATCH[2]}_${BASH_REMATCH[4]}.${BASH_REMATCH[5]}"
      if [ "$base" != "$dest" ]; then
        mv -f "$f" "$dir/$dest"
        if [[ "$dest" == *.changes ]]; then
          sed -i "s/${base%.changes}/${dest%.changes}/g" "$dir/$dest" || true
        fi
      fi
    fi
  done
  shopt -u nullglob
}

publish_deb_http() {
  local dir=$1
  local suite=$2
  local f base
  rewrite_changes_distribution "$dir" "$suite"
  normalize_deb_basenames "$dir"
  shopt -s nullglob
  for f in "$dir"/*.{deb,changes,buildinfo,ddeb}; do
    [ -f "$f" ] || continue
    base=$(basename "$f")
    curl -fsS -T "$f" "${REPODEB_URL%/}/upload/${suite}/${base}"
    echo "publish-private: PUT $base → ${REPODEB_URL%/}/upload/${suite}/"
  done
  shopt -u nullglob
  curl -fsS "${REPODEB_URL%/}/process?sync=1"
  echo "publish-private: process done (suite=$suite)"
}

publish_deb_dput() {
  local changes=$1
  local suite=${2:-}
  if [ -z "${DPUT_SSH_KEY:-}" ]; then
    echo "publish-private: skip dput (DPUT_SSH_KEY unset and REPODEB_URL unset)"
    return 0
  fi
  if [ -n "$suite" ]; then
    sed -i "s/^Distribution:.*/Distribution: ${suite}/" "$changes"
  fi
  local keyfile cf
  keyfile=$(mktemp)
  printf '%s\n' "$DPUT_SSH_KEY" >"$keyfile"
  chmod 600 "$keyfile"
  mkdir -p "$HOME/.ssh"
  cat >>"$HOME/.ssh/config" <<EOF
Host ${S1_HOST}
  IdentityFile ${keyfile}
  StrictHostKeyChecking accept-new
EOF
  cf=$(mktemp)
  local incoming=/home/instance/repodeb_aptly/data/upload
  if [ -n "$suite" ]; then
    incoming="${incoming}/${suite}"
  fi
  cat >"$cf" <<EOF
[s1]
method   = scp
fqdn     = ${S1_HOST}
login    = ${DPUT_SSH_USER:-lenik}
incoming = ${incoming}
allow_unsigned_uploads = 1
post_upload_command = ssh ${DPUT_SSH_USER:-lenik}@${S1_HOST} 'make -C /home/instance/repodeb_aptly process'
EOF
  dput -c "$cf" -f s1 "$changes"
  rm -f "$keyfile" "$cf"
}

publish_rpm() {
  local rpm=$1
  if [ -z "${REPORPM_URL:-}" ]; then
    echo "publish-private: skip rpm (REPORPM_URL unset)"
    return 0
  fi
  local base remote
  base=$(basename "$rpm")
  remote=${base#el*_}
  if [ -n "${REPORPM_USER:-}" ] && [ -n "${REPORPM_PASS:-}" ]; then
    curl -fsS -u "${REPORPM_USER}:${REPORPM_PASS}" \
      -T "$rpm" "${REPORPM_URL%/}/upload/${remote}"
    curl -fsS -u "${REPORPM_USER}:${REPORPM_PASS}" \
      "${REPORPM_URL%/}/rescan?sync=1" >/dev/null
  else
    echo "publish-private: warn: REPORPM_USER/PASS unset; trying anonymous PUT"
    curl -fsS -T "$rpm" "${REPORPM_URL%/}/upload/${remote}"
    curl -fsS "${REPORPM_URL%/}/rescan?sync=1" >/dev/null || true
  fi
  echo "publish-private: uploaded $remote"
}

# Forgejo NuGet (reponupkg_forgejo → repogit_forgejo packages).
publish_nupkg() {
  local nupkg=$1
  if [ -z "${REPONUPKG_URL:-}" ]; then
    echo "publish-private: skip nupkg (REPONUPKG_URL unset)"
    return 0
  fi
  if [ -z "${REPONUPKG_TOKEN:-}" ]; then
    echo "publish-private: ERROR: REPONUPKG_TOKEN required for $nupkg" >&2
    return 1
  fi
  local url owner base
  url=${REPONUPKG_URL%/}
  # Accept either .../nuget or .../nuget/index.json
  url=${url%/index.json}
  base=$(basename "$nupkg")
  owner=${REPONUPKG_OWNER:-}
  if [ -z "$owner" ] && [[ "$url" =~ /api/packages/([^/]+)/nuget ]]; then
    owner=${BASH_REMATCH[1]}
  fi
  owner=${owner:-lenik}
  # Prefer multipart form (Gitea/Forgejo); fall back to raw PUT + token auth.
  if curl -fsS -X PUT -u "${owner}:${REPONUPKG_TOKEN}" \
      -F "package=@${nupkg}" \
      "$url" ; then
    :
  else
    curl -fsS -X PUT \
      -H "Authorization: token ${REPONUPKG_TOKEN}" \
      -H "Content-Type: application/octet-stream" \
      --data-binary @"$nupkg" \
      "$url"
  fi
  echo "publish-private: uploaded nupkg $base → $url"
}

shopt -s nullglob
for nupkg in "$DIST_ROOT"/*.nupkg "$DIST_ROOT"/*/*.nupkg; do
  [ -f "$nupkg" ] || continue
  # Skip chocolatey staging copies under windows-manifests/choco if any
  case "$nupkg" in
    */windows-manifests/*) continue ;;
  esac
  publish_nupkg "$nupkg" || true
done

for z in "$DIST_ROOT"/*/*.zip "$DIST_ROOT"/*.zip; do
  [ -f "$z" ] || continue
  tmp=$(mktemp -d)
  unzip -q "$z" -d "$tmp"
  suite=""
  suite=$(infer_deb_suite "$z" || true)
  if [ -z "$suite" ]; then
    for sample in "$tmp"/*.{changes,deb}; do
      [ -f "$sample" ] || continue
      suite=$(infer_deb_suite "$sample" || true)
      [ -n "$suite" ] && break
    done
  fi
  if [ -n "$REPODEB_URL" ] && ls "$tmp"/*.changes >/dev/null 2>&1; then
    if [ -z "$suite" ]; then
      echo "publish-private: ERROR: cannot infer suite for $z (skip)" >&2
    else
      publish_deb_http "$tmp" "$suite" || true
    fi
  else
    for c in "$tmp"/*.changes; do
      [ -f "$c" ] || continue
      publish_deb_dput "$c" "$suite" || true
    done
  fi
  for r in "$tmp"/*.rpm; do
    [ -f "$r" ] || continue
    case "$r" in
      *.src.rpm) continue ;;
    esac
    publish_rpm "$r" || true
  done
  for nupkg in "$tmp"/*.nupkg; do
    [ -f "$nupkg" ] || continue
    publish_nupkg "$nupkg" || true
  done
  rm -rf "$tmp"
done
