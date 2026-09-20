#!/usr/bin/env bash
# Publish built packages to private repos (repodeb_aptly / reporpm_createrepo-c).
#
# Preferred (CI / anonymous):
#   REPODEB_URL=http://host:1130   — PUT /upload/ + GET /process?sync=1
#   REPORPM_URL=http://host:2505   — PUT /upload/ + GET /rescan?sync=1
#   REPORPM_USER / REPORPM_PASS    — required for reporpm (auth) unless
#                                    REPORPM_ANON=1 and the server allows it
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

publish_deb_http() {
  local dir=$1
  local f base
  shopt -s nullglob
  for f in "$dir"/*.{deb,changes,buildinfo,ddeb}; do
    [ -f "$f" ] || continue
    base=$(basename "$f")
    # Strip release-embedded names back? keep as-is; aptly uses basename.
    curl -fsS -T "$f" "${REPODEB_URL%/}/upload/${base}"
    echo "publish-private: PUT $base → ${REPODEB_URL%/}/upload/"
  done
  shopt -u nullglob
  curl -fsS "${REPODEB_URL%/}/process?sync=1"
  echo "publish-private: process done"
}

publish_deb_dput() {
  local changes=$1
  if [ -z "${DPUT_SSH_KEY:-}" ]; then
    echo "publish-private: skip dput (DPUT_SSH_KEY unset and REPODEB_URL unset)"
    return 0
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
  cat >"$cf" <<EOF
[s1]
method   = scp
fqdn     = ${S1_HOST}
login    = ${DPUT_SSH_USER:-lenik}
incoming = /home/instance/repodeb_aptly/data/upload
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

shopt -s nullglob
for z in "$DIST_ROOT"/*/*.zip "$DIST_ROOT"/*.zip; do
  [ -f "$z" ] || continue
  tmp=$(mktemp -d)
  unzip -q "$z" -d "$tmp"
  if [ -n "$REPODEB_URL" ] && ls "$tmp"/*.changes >/dev/null 2>&1; then
    publish_deb_http "$tmp" || true
  else
    for c in "$tmp"/*.changes; do
      [ -f "$c" ] || continue
      publish_deb_dput "$c" || true
    done
  fi
  for r in "$tmp"/*.rpm; do
    [ -f "$r" ] || continue
    case "$r" in
      *.src.rpm) continue ;;
    esac
    publish_rpm "$r" || true
  done
  rm -rf "$tmp"
done
