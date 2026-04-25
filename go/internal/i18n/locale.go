// Copyright (C) 2026 Lenik <zephyr@bodz.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

package i18n

import (
	"os"
	"strings"
)

// LocaleTag returns a rough locale tag (e.g. "ja", "zh_CN") for selecting a .po file.
// It prefers LANGUAGE, then LC_ALL, LC_MESSAGES, LANG, matching the usual gettext
// environment ordering.
func LocaleTag() string {
	keys := []string{"LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"}
	for _, k := range keys {
		v := os.Getenv(k)
		if v == "" || v == "C" || v == "POSIX" {
			continue
		}
		if k == "LANGUAGE" {
			// e.g. "de:fr" — first is preferred
			if i := strings.IndexByte(v, ':'); i >= 0 {
				v = v[:i]
			}
		}
		// de_DE.utf-8, zh_CN.utf-8, etc.
		if i := strings.IndexByte(v, '.'); i >= 0 {
			v = v[:i]
		}
		if i := strings.IndexByte(v, '@'); i >= 0 {
			v = v[:i]
		}
		// "zh-TW" style is uncommon for our po names; keep underscore form.
		v = strings.ReplaceAll(v, "-", "_")
		return strings.TrimSpace(v)
	}
	return "C"
}
