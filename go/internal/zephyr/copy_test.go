// Copyright (C) 2026 Lenik <zephyr@bodz.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

package zephyr_test

import (
	"bytes"
	"io"
	"strings"
	"testing"

	"github.com/lenik/zephyr/internal/zephyr"
)

func TestCopyStreamSuccess(t *testing.T) {
	in := strings.NewReader("alpha\nbeta\n")
	var out bytes.Buffer
	if err := zephyr.CopyStream(in, &out); err != nil {
		t.Fatal(err)
	}
	if got := out.String(); got != "alpha\nbeta\n" {
		t.Fatalf("got %q want %q", got, "alpha\nbeta\n")
	}
}

func TestCopyStreamEmpty(t *testing.T) {
	if err := zephyr.CopyStream(strings.NewReader(""), io.Discard); err != nil {
		t.Fatal(err)
	}
}

func TestCopyFileMissing(t *testing.T) {
	err := zephyr.CopyFileToStdout(io.Discard, "/definitely/not/found")
	if err == nil {
		t.Fatal("expected error")
	}
}
