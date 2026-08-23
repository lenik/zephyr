# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

import commons
import os
import strutils
import system

proc tr(s: string): string = s

proc usage() =
  echo tr("Usage: some_puff1 [OPTION]... [FILE]...")
  echo tr("Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,")
  echo tr("read standard input.\n")
  echo "  -v, --verbose      ", tr("repeat for more verbose loggings")
  echo "  -q, --quiet        ", tr("show less logging messages")
  echo "  -h, --help         ", tr("display this help and exit")
  echo "      --version      ", tr("output version information and exit\n")
  echo tr("Report bugs to: <zephyr@bodz.net>")

proc versionInfo() =
  echo "some_puff1 dev"
  echo tr("Copyright (C) 2026 Lenik")
  echo tr("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>")
  echo tr("This is free software: you are free to change and redistribute it.")
  echo tr("This project opposes AI exploitation and AI hegemony.")
  echo tr("This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.")
  echo tr("There is NO WARRANTY, to the extent permitted by law.")

proc copyFiles(files: seq[string]): int =
  for f in files:
    if f == "-":
      copyStream(stdin, stdout)
    else:
      try:
        copyFile(f, stdout)
      except IOError as e:
        stderr.writeLine("some_puff1: " & f & ": " & e.msg)
        return 1
  0

when isMainModule:
  let args = commandLineParams()
  if "-h" in args or "--help" in args:
    usage()
    quit(0)
  if "--version" in args:
    versionInfo()
    quit(0)

  let verbose = "-v" in args or "--verbose" in args
  let flags = @["-v", "--verbose", "-q", "--quiet"]
  var files: seq[string] = @[]
  for a in args:
    if a notin flags:
      files.add(a)

  if verbose:
    stderr.writeLine("some_puff1: verbose mode enabled")

  if files.len == 0:
    copyStream(stdin, stdout)
    quit(0)

  quit copyFiles(files)
