// Copyright (C) 2026 Lenik <zephyr@bodz.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

// Package zephyr provides small helpers shared by zephyr CLIs (a cat-like file copy, etc.).
package zephyr

import (
	"io"
	"os"
)

// bufSize matches the original C example (8 KiB) for no particular reason.
const bufSize = 8192

// CopyStream copies from r to w using a fixed buffer size, like the template's C version.
func CopyStream(r io.Reader, w io.Writer) error {
	buf := make([]byte, bufSize)
	for {
		n, rerr := r.Read(buf)
		if n > 0 {
			if _, werr := w.Write(buf[:n]); werr != nil {
				return werr
			}
		}
		if rerr != nil {
			if rerr == io.EOF {
				return nil
			}
			return rerr
		}
	}
}

// CopyFileToStdout copies path to w (the template wrote to stdout) and returns an
// error suitable for [fmt.Errorf] and %w, including [os.PathError] / write failures.
func CopyFileToStdout(w io.Writer, path string) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	return CopyStream(f, w)
}
