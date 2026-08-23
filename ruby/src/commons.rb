# Copyright (C) 2026 Lenik <zephyr@bodz.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

module Commons
  module_function

  def copy_stream(inp, out)
    while (chunk = inp.read(8192))
      out.write(chunk)
    end
    true
  rescue StandardError
    false
  end

  def copy_file(prog, path)
    File.open(path, 'rb') do |fh|
      return false unless copy_stream(fh, $stdout)
    end
    true
  rescue Errno::ENOENT, Errno::EACCES => e
    warn "#{prog}: #{path}: #{e.message}"
    false
  rescue StandardError
    warn "#{prog}: write error"
    false
  end
end
