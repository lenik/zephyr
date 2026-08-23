# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import strutils
import unittest

import commons

suite "commons":
  test "copyStream roundtrip":
    let tmpIn = getTempDir() / "some_puff1-in.txt"
    let tmpOut = getTempDir() / "some_puff1-out.txt"
    writeFile(tmpIn, "alpha\nbeta\n")
    let src = open(tmpIn, fmRead)
    let dst = open(tmpOut, fmWrite)
    copyStream(src, dst)
    src.close()
    dst.close()
    check readFile(tmpOut) == "alpha\nbeta\n"
    removeFile(tmpIn)
    removeFile(tmpOut)
