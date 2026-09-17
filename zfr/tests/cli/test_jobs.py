# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for zfr_lib.jobs helpers."""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import add_src_to_path

add_src_to_path()

from zfr_lib.jobs import (  # noqa: E402
    add_job_argument,
    debuild_jobs_args,
    jobs_is_auto,
    split_job_budget,
)


class JobBudgetTests(unittest.TestCase):
    def test_auto_stays_none_per_worker(self) -> None:
        self.assertEqual(split_job_budget(None, 3), [None, None, None])
        self.assertEqual(split_job_budget(0, 2), [None, None])

    def test_sequential_gets_full_budget(self) -> None:
        self.assertEqual(split_job_budget(8, 1), [8])

    def test_splits_evenly_across_workers(self) -> None:
        self.assertEqual(split_job_budget(8, 3), [3, 3, 2])
        self.assertEqual(split_job_budget(9, 3), [3, 3, 3])

    def test_each_share_at_least_one(self) -> None:
        self.assertEqual(split_job_budget(2, 5), [1, 1, 1, 1, 1])

    def test_debuild_auto_is_bare_j(self) -> None:
        self.assertEqual(debuild_jobs_args(None), ["-j"])
        self.assertEqual(debuild_jobs_args(4), ["-j4"])
        self.assertTrue(jobs_is_auto(None))
        self.assertFalse(jobs_is_auto(4))

    def test_cli_bare_j_is_auto(self) -> None:
        p = argparse.ArgumentParser()
        add_job_argument(p)
        self.assertIsNone(p.parse_args([]).jobs)
        self.assertIsNone(p.parse_args(["-j"]).jobs)
        self.assertEqual(p.parse_args(["-j", "8"]).jobs, 8)
        self.assertEqual(p.parse_args(["--job", "4"]).jobs, 4)


if __name__ == "__main__":
    unittest.main()
