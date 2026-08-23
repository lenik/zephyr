{ Copyright (C) 2026 Lenik <zephyr@bodz.net> }
{ SPDX-License-Identifier: AGPL-3.0-or-later }

program test_commons;

{$mode objfpc}{$H+}

uses
  SysUtils,
  commons;

var
  fin, fout: Text;
  tmpin, tmpout: string;
begin
  tmpin := GetTempDir + DirectorySeparator + 'some_puff1-in.txt';
  tmpout := GetTempDir + DirectorySeparator + 'some_puff1-out.txt';
  Assign(fin, tmpin);
  Rewrite(fin);
  WriteLn(fin, 'alpha');
  WriteLn(fin, 'beta');
  Close(fin);

  Assign(fin, tmpin);
  Reset(fin);
  Assign(fout, tmpout);
  Rewrite(fout);
  if not copy_stream(fin, fout) then
    Halt(1);
  Close(fin);
  Close(fout);

  Assign(fout, tmpout);
  Reset(fout);
  if not ReadLn(fout).Equals('alpha') then
    Halt(2);
  if not ReadLn(fout).Equals('beta') then
    Halt(3);
  Close(fout);

  DeleteFile(tmpin);
  DeleteFile(tmpout);
end.
