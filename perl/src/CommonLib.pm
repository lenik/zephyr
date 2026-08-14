# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

package CommonLib;

use strict;
use warnings;
use Exporter qw(import);

our @EXPORT_OK = qw(copy_stream copy_file);

sub copy_stream {
    my ($in, $out) = @_;
    my $buf;
    while (read($in, $buf, 8192)) {
        print {$out} $buf or return 0;
    }
    return 1;
}

sub copy_file {
    my ($prog, $path) = @_;
    open my $fh, '<:raw', $path or do {
        warn "$prog: $path: $!\n";
        return 0;
    };
    my $ok = copy_stream($fh, \*STDOUT);
    close $fh or $ok = 0;
    if (!$ok) {
        warn "$prog: write error\n";
        return 0;
    }
    return 1;
}

1;
