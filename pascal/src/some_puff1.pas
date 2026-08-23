{ Copyright (C) 2026 Lenik <zephyr@bodz.net> }
{ SPDX-License-Identifier: AGPL-3.0-or-later }

program some_puff1;

{$mode objfpc}{$H+}

uses
  SysUtils,
  commons;

procedure usage;
begin
  WriteLn('Usage: some_puff1 [OPTION]... [FILE]...');
  WriteLn('Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,');
  WriteLn('read standard input.');
  WriteLn;
  WriteLn('  -v, --verbose      repeat for more verbose loggings');
  WriteLn('  -q, --quiet        show less logging messages');
  WriteLn('  -h, --help         display this help and exit');
  WriteLn('      --version      output version information and exit');
  WriteLn;
  WriteLn('Report bugs to: <zephyr@bodz.net>');
end;

procedure show_version;
begin
  WriteLn('some_puff1 dev');
  WriteLn('Copyright (C) 2026 Lenik');
  WriteLn('License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>');
end;

var
  i, verbose: Integer;
  files: array of string;
begin
  verbose := 0;
  SetLength(files, 0);
  for i := 1 to ParamCount do
  begin
    if (ParamStr(i) = '-h') or (ParamStr(i) = '--help') then
    begin
      usage;
      Halt(0);
    end
    else if ParamStr(i) = '--version' then
    begin
      show_version;
      Halt(0);
    end
    else if (ParamStr(i) = '-v') or (ParamStr(i) = '--verbose') then
      Inc(verbose)
    else if (ParamStr(i) = '-q') or (ParamStr(i) = '--quiet') then
      verbose := -1
    else
    begin
      SetLength(files, Length(files) + 1);
      files[High(files)] := ParamStr(i);
    end;
  end;

  if verbose > 0 then
    WriteLn(StdErr, 'some_puff1: verbose mode enabled');

  if Length(files) = 0 then
  begin
    if verbose > 0 then
      WriteLn(StdErr, 'some_puff1: reading from standard input');
    if not copy_stream(Input, Output) then
      Halt(1);
    Halt(0);
  end;

  for i := 0 to High(files) do
  begin
    if files[i] = '-' then
    begin
      if verbose > 0 then
        WriteLn(StdErr, 'some_puff1: copying from standard input');
      if not copy_stream(Input, Output) then
        Halt(1);
    end
    else
    begin
      if verbose > 0 then
        WriteLn(StdErr, 'some_puff1: copying from ', files[i]);
      if not copy_file(files[i], Output) then
        Halt(1);
    end;
  end;
end.
