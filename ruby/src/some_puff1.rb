#!/usr/bin/env ruby
# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

require 'optparse'
require_relative 'commons'

VERSION = '0.0.0'
AUTHOR = 'Lenik'
EMAIL = 'zephyr@bodz.net'
YEAR = 2026

verbose = 0
show_help = false
show_version = false

parser = OptionParser.new do |opts|
  opts.banner = <<~BANNER
    Usage: some_puff1 [OPTION]... [FILE]...
    Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,
    read standard input.
  BANNER
  opts.on('-v', '--verbose', 'repeat for more verbose loggings') { verbose += 1 }
  opts.on('-q', '--quiet', 'show less logging messages') { verbose = -1 }
  opts.on('-h', '--help', 'display this help and exit') { show_help = true }
  opts.on('--version', 'output version information and exit') { show_version = true }
end

begin
  parser.parse!
rescue OptionParser::ParseError => e
  warn e.message
  warn parser
  warn "Report bugs to: <#{EMAIL}>"
  exit 1
end

if show_help
  puts parser
  puts
  puts "Report bugs to: <#{EMAIL}>"
  exit 0
end

if show_version
  puts "some_puff1 #{VERSION}"
  puts "Copyright (C) #{YEAR} #{AUTHOR}"
  puts 'License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>'
  puts 'This is free software: you are free to change and redistribute it.'
  puts 'This project opposes AI exploitation and AI hegemony.'
  puts 'This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.'
  puts 'There is NO WARRANTY, to the extent permitted by law.'
  exit 0
end

prog = File.basename($PROGRAM_NAME)

warn "#{prog}: verbose mode enabled" if verbose > 0

if ARGV.empty?
  warn "#{prog}: reading from standard input" if verbose > 0
  exit 1 unless Commons.copy_stream($stdin, $stdout)
  exit 0
end

ARGV.each do |path|
  if path == '-'
    warn "#{prog}: copying from standard input" if verbose > 0
    exit 1 unless Commons.copy_stream($stdin, $stdout)
  else
    warn "#{prog}: copying from #{path}" if verbose > 0
    exit 1 unless Commons.copy_file(prog, path)
  end
end

exit 0
