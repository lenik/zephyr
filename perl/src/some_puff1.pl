#!/usr/bin/env perl
# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

use strict;
use warnings;
use FindBin;
use lib "$FindBin::RealBin", "$FindBin::RealBin/../lib";
use Getopt::Long qw(:config bundling no_ignore_case);
use Commons qw(copy_stream copy_file);

my $VERSION = '0.0.0';
my $AUTHOR  = 'Lenik';
my $EMAIL   = 'zephyr@bodz.net';
my $YEAR    = 2026;

my $verbose = 0;
my $help    = 0;
my $version = 0;

GetOptions(
    'v|verbose+' => \$verbose,
    'q|quiet'    => sub { $verbose = -1 },
    'h|help'     => \$help,
    'version'    => \$version,
) or do {
    usage(*STDERR);
    exit 1;
};

if ($help) {
    usage(*STDOUT);
    exit 0;
}
if ($version) {
    print "some_puff1 $VERSION\n";
    print "Copyright (C) $YEAR $AUTHOR\n";
    print "License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n";
    print "This is free software: you are free to change and redistribute it.\n";
    print "This project opposes AI exploitation and AI hegemony.\n";
    print "This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.\n";
    print "There is NO WARRANTY, to the extent permitted by law.\n";
    exit 0;
}

my $prog = $0;
$prog =~ s{.*/}{};

if ($verbose > 0) {
    print STDERR "$prog: verbose mode enabled\n";
}

if (!@ARGV) {
    print STDERR "$prog: reading from standard input\n" if $verbose > 0;
    copy_stream(\*STDIN, \*STDOUT) or exit 1;
    exit 0;
}

for my $path (@ARGV) {
    if ($path eq '-') {
        print STDERR "$prog: copying from standard input\n" if $verbose > 0;
        copy_stream(\*STDIN, \*STDOUT) or exit 1;
    }
    else {
        print STDERR "$prog: copying from $path\n" if $verbose > 0;
        copy_file($prog, $path) or exit 1;
    }
}

exit 0;

sub usage {
    my ($out) = @_;
    print $out <<'EOF';
Usage: some_puff1 [OPTION]... [FILE]...
Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,
read standard input.

  -v, --verbose      repeat for more verbose loggings
  -q, --quiet        show less logging messages
  -h, --help         display this help and exit
      --version      output version information and exit

EOF
    print $out "Report bugs to: <$EMAIL>\n";
}
