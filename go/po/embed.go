// Copyright (C) 2026 Lenik <zephyr@bodz.net>
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Package po holds embedded GNU gettext .po message catalogs.
package po

import "embed"

//go:embed *.po
var Files embed.FS
