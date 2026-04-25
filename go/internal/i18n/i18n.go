// Copyright (C) 2026 Lenik <zephyr@bodz.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

package i18n

import (
	"strings"

	"github.com/leonelquinteros/gotext"

	"github.com/lenik/zephyr/po"
)

var dict = gotext.NewPo()

// Init loads the .po for the current locale. Safe to call more than once.
func Init() {
	dict = gotext.NewPo()
	loc := LocaleTag()
	if loc == "C" || loc == "POSIX" || loc == "en" {
		return
	}

	try := []string{loc + ".po"}
	// e.g. de_DE -> de, zh_Hant -> zh, etc.
	if i := strings.IndexByte(loc, '_'); i > 0 {
		try = append(try, loc[:i]+".po")
	}

	p := gotext.NewPo()
	for _, name := range try {
		b, err := po.Files.ReadFile(name)
		if err != nil {
			continue
		}
		p.Parse(b)
		dict = p
		return
	}
}

// T returns the translation for a single id (GNU gettext id is usually English).
func T(s string) string {
	return dict.Get(s)
}

// Tfc returns a translated, printf-style string.
func Tfc(s string, args ...any) string {
	return dict.Get(s, args...)
}
