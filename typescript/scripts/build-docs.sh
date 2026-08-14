#!/usr/bin/env bash
# Build man(1) and info pages from AsciiDoc via Asciidoctor.
# Usage: build-docs.sh <some_puff1.adoc> <outdir> <version> <year> <author> <email>
set -euo pipefail

adoc=$1
outdir=$2
version=$3
year=$4
author=$5
email=$6

mkdir -p "$outdir"

attrs=(
  -a "project-version=${version}"
  -a "project-year=${year}"
  -a "project-author=${author}"
  -a "project-email=${email}"
)

asciidoctor -b manpage "${attrs[@]}" -o "${outdir}/some_puff1.1" "$adoc"

# Info: render as article HTML, convert to Texinfo, compile with makeinfo.
html="${outdir}/some_puff1.doc.html"
texi="${outdir}/some_puff1.texi"
asciidoctor -b html5 -a doctype=article -a 'doctitle=some_puff1' "${attrs[@]}" \
  -o "$html" "$adoc"

{
  printf '%s\n' '\input texinfo'
  printf '%s\n' '@setfilename some_puff1.info'
  printf '%s\n' '@settitle some_puff1'
  printf '%s\n' '@documentencoding UTF-8'
  printf '\n'
  pandoc "$html" -f html -t texinfo --top-level-division=chapter
  printf '\n%s\n' '@bye'
} >"$texi"

makeinfo --no-split --force -o "${outdir}/some_puff1.info" "$texi"
rm -f "$html" "$texi"
