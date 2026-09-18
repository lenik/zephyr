#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Sync gettext catalogs from current sources (meson run_target posync).
set -euo pipefail
SOURCE_ROOT="${1:-${MESON_SOURCE_ROOT:-.}}"
cd "$SOURCE_ROOT/po"
mapfile -t py_files < <(find ../src -name '*.py' | sort)
xgettext --from-code=UTF-8 --keyword=_ --language=Python --directory=.. \
    --output=zephyr.pot "${py_files[@]#../}"
while IFS= read -r lang; do
    [ -n "$lang" ] || continue
    case "$lang" in
        '#'* ) continue ;;
    esac
    po_file="$lang.po"
    if [ ! -f "$po_file" ]; then
        msginit --no-translator --input=zephyr.pot --locale="$lang" --output-file="$po_file"
    fi
    msgmerge --update --backup=none "$po_file" zephyr.pot
    msgattrib --no-obsolete --output-file="$po_file" "$po_file"
done < LINGUAS
