# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for foreach-style Meson man target helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.ize.man import (  # noqa: E402
    ensure_meson_man_targets,
    has_foreach_man_targets,
    man_foreach_block,
    strip_individual_man_targets,
)


_FOREACH = """
foreach puff : apps.keys()
    custom_target(
        puff + '-man',
        input: 'docs' / (puff + '.adoc'),
        output: puff + '.1',
        command: [asciidoctor, '-b', 'manpage', '-o', '@OUTPUT@', '@INPUT@'],
        install: true,
        install_dir: mandir / 'man1',
    )
endforeach
"""

_INDIVIDUAL = """
custom_target(
    'gh-makerelease-man',
    input: 'docs/gh-makerelease.adoc',
    output: 'gh-makerelease.1',
    command: [
        asciidoctor,
        '-b', 'manpage',
        '-a', 'project-version=' + meson.project_version(),
        '-a', 'project-year=@0@'.format(project_year),
        '-a', 'project-author=' + project_author,
        '-a', 'project-email=' + project_email,
        '-o', '@OUTPUT@',
        '@INPUT@',
    ],
    build_by_default: true,
    install: true,
    install_dir: mandir / 'man1',
)
"""


class MesonManForeachTests(unittest.TestCase):
    def test_detects_foreach_expression_targets(self) -> None:
        self.assertTrue(has_foreach_man_targets(_FOREACH))
        self.assertFalse(has_foreach_man_targets(_INDIVIDUAL))

    def test_skips_append_when_foreach_present(self) -> None:
        text = "project('demo')\n" + _FOREACH + _INDIVIDUAL
        new, details = ensure_meson_man_targets(
            text, ["gh-makerelease", "gh-refresh-contributors"]
        )
        self.assertTrue(has_foreach_man_targets(new))
        self.assertNotIn("'gh-makerelease-man'", new)
        self.assertTrue(any("duplicate" in d for d in details))

    def test_adds_foreach_when_missing(self) -> None:
        text = "project('demo')\nasciidoctor = find_program('asciidoctor')\n"
        new, details = ensure_meson_man_targets(text, ["tool-a", "tool-b"])
        self.assertIn("man_puffs", new)
        self.assertIn("puff + '-man'", new)
        self.assertIn("'tool-a'", new)
        self.assertTrue(any("foreach" in d for d in details))
        self.assertNotIn("'tool-a-man'", new)

    def test_strip_individual(self) -> None:
        cleaned, removed = strip_individual_man_targets("x\n" + _INDIVIDUAL + "\ny\n")
        self.assertEqual(removed, ["gh-makerelease"])
        self.assertNotIn("custom_target", cleaned)

    def test_man_foreach_block_shape(self) -> None:
        block = man_foreach_block(["a", "b"])
        self.assertIn("foreach puff : man_puffs", block)
        self.assertIn("puff + '-man'", block)


if __name__ == "__main__":
    unittest.main()
