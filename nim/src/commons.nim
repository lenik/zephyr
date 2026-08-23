# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

proc copyStream*(src, dst: File) =
  var buf = newString(8192)
  while true:
    let n = src.readBuffer(addr buf[0], buf.len)
    if n <= 0:
      break
    dst.writeBuffer(addr buf[0], n)
    dst.flush()

proc copyFile*(path: string, dst: File) =
  let src = open(path, fmRead)
  defer: src.close()
  copyStream(src, dst)
