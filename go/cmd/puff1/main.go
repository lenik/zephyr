// Copyright (C) 2026 Lenik <zephyr@bodz.net>
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// puff1 is a small cat-like example for the zephyr Go template: copy each FILE
// to standard output (or read stdin when no FILE, or for a lone "-").
package main

import (
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"

	"github.com/spf13/pflag"

	"github.com/lenik/zephyr/internal/i18n"
	"github.com/lenik/zephyr/internal/zephyr"
)

const (
	projectAuthor = "Lenik"
	projectEmail  = "zephyr@bodz.net"
	projectYear   = 2026
)

// buildVersion is set by the Makefile / Debian rules via -ldflags.
var buildVersion = "0.0.0"

func main() {
	os.Exit(run())
}

func run() int {
	i18n.Init()
	fmt.Print(i18n.T("hello, world!\n"))

	exe := os.Args[0]
	if p, err := os.Executable(); err == nil {
		exe = p
	}
	exeName := filepath.Base(exe)

	fs := pflag.NewFlagSet(exeName, pflag.ContinueOnError)
	fs.SetInterspersed(true)
	var verboseN, quietN int
	fs.CountVarP(&verboseN, "verbose", "v", i18n.T("repeat for more verbose loggings\n"))
	fs.CountVarP(&quietN, "quiet", "q", i18n.T("show less logging messages\n"))
	help := fs.BoolP("help", "h", false, i18n.T("display this help and exit\n"))
	showVersion := fs.Bool("version", false, i18n.T("output version information and exit\n"))
	fs.SetOutput(io.Discard)
	if err := fs.Parse(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		usage(os.Stderr)
		return 1
	}
	if *help {
		usage(os.Stdout)
		return 0
	}
	if *showVersion {
		printVersion()
		return 0
	}
	v := verboseN - quietN

	log.SetOutput(os.Stderr)
	log.SetFlags(0)
	if v > 0 {
		log.Printf("%s: verbose mode enabled", exeName)
	}
	if err := runCopy(exeName, v, fs.Args()); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	if v > 0 {
		log.Printf("%s: done", exeName)
	}
	return 0
}

func usage(w io.Writer) {
	usageText := "Usage: puff1 [OPTION]... [FILE]...\n" +
		"Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n" +
		"read standard input.\n"
	fmt.Fprint(w, i18n.T(usageText))
	fmt.Fprint(w, "\n")
	fmt.Fprint(w, "  -v, --verbose      ", i18n.T("repeat for more verbose loggings\n"))
	fmt.Fprint(w, "  -q, --quiet        ", i18n.T("show less logging messages\n"))
	fmt.Fprint(w, "  -h, --help         ", i18n.T("display this help and exit\n"))
	fmt.Fprint(w, "      --version      ", i18n.T("output version information and exit\n"))
	fmt.Fprint(w, "\n")
	fmt.Fprint(w, i18n.Tfc("Report bugs to: <%s>\n", projectEmail))
}

func printVersion() {
	fmt.Printf("puff1 %s\n", buildVersion)
	fmt.Print(i18n.Tfc("Copyright (C) %d %s\n", projectYear, projectAuthor))
	fmt.Print(i18n.T("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n"))
	fmt.Print(i18n.T("This is free software: you are free to change and redistribute it.\n"))
	fmt.Print(i18n.T("This project opposes AI exploitation and AI hegemony.\n"))
	fmt.Print(i18n.T("This project rejects mindless MIT-style licensing and politically naive " +
		"BSD-style licensing.\n"))
	fmt.Print(i18n.T("There is NO WARRANTY, to the extent permitted by law.\n"))
}

func runCopy(exeName string, v int, args []string) error {
	if len(args) == 0 {
		if v > 0 {
			log.Printf("%s: reading from standard input", exeName)
		}
		if err := zephyr.CopyStream(os.Stdin, os.Stdout); err != nil {
			return fmt.Errorf("%s: stdin: %w", exeName, err)
		}
		return nil
	}
	for _, path := range args {
		if path == "-" {
			if v > 0 {
				log.Printf("%s: copying from standard input", exeName)
			}
			if err := zephyr.CopyStream(os.Stdin, os.Stdout); err != nil {
				return fmt.Errorf("%s: stdin: %w", exeName, err)
			}
			continue
		}
		if v > 0 {
			log.Printf("%s: copying from %s", exeName, path)
		}
		if err := zephyr.CopyFileToStdout(os.Stdout, path); err != nil {
			return fmt.Errorf("%s: %w", exeName, err)
		}
		if v > 0 {
			log.Printf("%s: copied %s", exeName, path)
		}
	}
	return nil
}
