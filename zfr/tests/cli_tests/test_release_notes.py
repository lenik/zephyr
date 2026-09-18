# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for aggregated GitHub release notes from debian/changelog."""

from __future__ import annotations

import unittest

from release.gh_release import (
    format_release_notes,
    normalize_release_version,
    parse_debian_changelog,
    stanzas_since_last_release,
)

SAMPLE = """\
zephyr (1.6.0) testing; urgency=medium

  * Ship the big feature.
  * Fix the docs.

 -- Lenik <lenik@bodz.net>  Fri, 18 Sep 2026 12:00:00 +0800

zephyr (1.5.0) testing; urgency=medium

  * Internal polish.
  * More tests that
    span two lines.

 -- Lenik <lenik@bodz.net>  Thu, 17 Sep 2026 12:00:00 +0800

zephyr (1.4.0) testing; urgency=medium

  * Mid release.

 -- Lenik <lenik@bodz.net>  Wed, 16 Sep 2026 12:00:00 +0800

zephyr (1.2.0) testing; urgency=medium

  * Last published on GitHub.

 -- Lenik <lenik@bodz.net>  Tue, 15 Sep 2026 12:00:00 +0800
"""


class ReleaseNotesAggregateTests(unittest.TestCase):
    def test_normalize(self) -> None:
        self.assertEqual(normalize_release_version("v1.6.0"), "1.6.0")
        self.assertEqual(normalize_release_version("1:1.6.0-1"), "1.6.0")

    def test_parse_and_aggregate(self) -> None:
        stanzas = parse_debian_changelog(SAMPLE)
        self.assertEqual(
            [normalize_release_version(s.version) for s in stanzas],
            ["1.6.0", "1.5.0", "1.4.0", "1.2.0"],
        )
        self.assertEqual(
            stanzas[1].bullets,
            ("Internal polish.", "More tests that span two lines."),
        )
        selected = stanzas_since_last_release(
            stanzas, current_version="1.6.0", since_version="1.2.0"
        )
        self.assertEqual(
            [normalize_release_version(s.version) for s in selected],
            ["1.6.0", "1.5.0", "1.4.0"],
        )
        notes = format_release_notes(selected)
        self.assertIn("Release 1.6.0\n\n- Ship the big feature.", notes)
        self.assertIn("Internal Version 1.5.0\n\n- Internal polish.", notes)
        self.assertIn("Internal Version 1.4.0\n\n- Mid release.", notes)
        self.assertNotIn("1.2.0", notes)
        self.assertTrue(notes.endswith("See README.md and debian/changelog.\n"))

    def test_no_prior_release_uses_current_only(self) -> None:
        stanzas = parse_debian_changelog(SAMPLE)
        selected = stanzas_since_last_release(
            stanzas, current_version="1.6.0", since_version=None
        )
        self.assertEqual(
            [normalize_release_version(s.version) for s in selected],
            ["1.6.0"],
        )


if __name__ == "__main__":
    unittest.main()
