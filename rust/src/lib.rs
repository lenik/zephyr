// SPDX-License-Identifier: AGPL-3.0-or-later

use std::fs::File;
use std::io::{self, Read, Write};
use std::path::Path;
use thiserror::Error;

/// Copy up to the next chunk size from `reader` to `writer`. Returns `Ok(true)` if more data
/// may follow, or `Ok(false)` at end of input. Uses the same 8 KiB buffer size as the original C
/// template for predictable behaviour in tests and callers that wrap this in a loop.
const CHUNK: usize = 8192;

#[derive(Error, Debug)]
pub enum Puff1Error {
    #[error("I/O error: {0}")]
    Io(#[from] io::Error),
}

/// Copy from `input` to `output` in fixed-size chunks. Returns `Err` on read or write failure.
pub fn copy_stream(input: &mut impl Read, output: &mut impl Write) -> Result<(), Puff1Error> {
    let mut buf = [0u8; CHUNK];
    loop {
        let n = input.read(&mut buf)?;
        if n == 0 {
            return Ok(());
        }
        output.write_all(&buf[..n])?;
    }
}

/// Copy a regular file to `output`, or return an error if the file cannot be read.
pub fn copy_file_to_writer<P: AsRef<Path>>(
    _prog: &str,
    path: P,
    output: &mut impl Write,
) -> Result<(), Puff1Error> {
    let path = path.as_ref();
    let mut f = File::open(path)?;
    copy_stream(&mut f, output)?;
    Ok(())
}

/// Read `path` and write the contents to `stdout` (line-buffered lock). Matches the C template’s
/// `copy_file` behaviour, including the same I/O error surface for callers.
pub fn copy_file_to_stdout(prog: &str, path: &Path) -> Result<(), Puff1Error> {
    let out = io::stdout();
    let mut out = out.lock();
    copy_file_to_writer(prog, path, &mut out)
}

#[cfg(test)]
mod tests {
    use super::*;

    use std::io::Cursor;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn copy_stream_success() {
        let text: &[u8] = b"alpha\nbeta\n";
        let mut in_ = Cursor::new(text);
        let mut out = Vec::new();
        copy_stream(&mut in_, &mut out).unwrap();
        assert_eq!(out, text);
    }

    #[test]
    fn copy_file_missing() {
        let p = std::env::temp_dir().join(format!(
            "puff1-definitely-missing-{}",
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let r = copy_file_to_writer("puff1-test", &p, &mut Vec::new());
        assert!(r.is_err());
    }
}
