{ Copyright (C) 2026 Lenik <zephyr@bodz.net> }
{ SPDX-License-Identifier: AGPL-3.0-or-later }

unit commons;

interface
  procedure copy_stream;
  procedure copy_file;
end;

implementation

function copy_stream(src, dst: Text): Boolean;
var
  buf: array[0..8191] of Char;
  n: LongInt;
begin
  repeat
    n := src.ReadBuffer(buf, SizeOf(buf));
    if n > 0 then
    begin
      dst.WriteBuffer(buf, n);
      if dst.Error <> 0 then
        Exit(False);
    end;
  until n <= 0;
  Result := src.Error = 0;
end;

function copy_file(const path: AnsiString; dst: Text): Boolean;
var
  f: File;
begin
  Assign(f, path);
  Reset(f, 1);
  if IOResult <> 0 then
    Exit(False);
  Result := copy_stream(f, dst);
  Close(f);
end;

end.
