#!/bin/sh
# Install the release puff1 binary to the path given as $1. Meson provides the
# final install path; we always build to ${MESON_BUILD_DIR}/cargo-target.
set -euf
out="$1"
root="$2"
b="$3"
export CARGO_TARGET_DIR="${b}/cargo-target"
# Avoid broken sccache in some environments; Meson can override via env in tests.
[ "${ZEPHYR_CARGO_ENABLE_SCCACHE:-0}" = 1 ] || unset RUSTC_WRAPPER
cd "$root"
cargo build --release --locked --bin puff1
install -m755 "${CARGO_TARGET_DIR}/release/puff1" "${out}.tmp"
mv -f "${out}.tmp" "${out}"
