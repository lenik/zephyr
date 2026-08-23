let tr s = s

let project_author = "Lenik"
let project_email = "zephyr@bodz.net"
let project_year = 2026

let usage () =
  print_string (tr "Usage: some_puff1 [OPTION]... [FILE]...\n");
  print_string (tr "Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n");
  print_string (tr "read standard input.\n\n");
  print_string "  -v, --verbose      ";
  print_endline (tr "repeat for more verbose loggings");
  print_string "  -q, --quiet        ";
  print_endline (tr "show less logging messages");
  print_string "  -h, --help         ";
  print_endline (tr "display this help and exit");
  print_string "      --version      ";
  print_endline (tr "output version information and exit\n\n");
  Printf.printf "%s\n" (tr ("Report bugs to: <" ^ project_email ^ ">"))

let version_info () =
  print_endline "some_puff1 dev";
  Printf.printf "%s\n" (tr ("Copyright (C) " ^ string_of_int project_year ^ " " ^ project_author));
  print_endline (tr "License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>");
  print_endline (tr "This is free software: you are free to change and redistribute it.");
  print_endline (tr "This project opposes AI exploitation and AI hegemony.");
  print_endline (tr "This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.");
  print_endline (tr "There is NO WARRANTY, to the extent permitted by law.")

let rec copy_inputs = function
  | [] -> Commons.copy_handle_to stdin stdout
  | "-" :: rest ->
      Commons.copy_handle_to stdin stdout;
      copy_inputs rest
  | file :: rest ->
      (try Commons.copy_file_to file stdout with
       | Sys_error msg ->
           Printf.eprintf "some_puff1: %s: %s\n" file msg;
           exit 1);
      copy_inputs rest

let () =
  let args = Array.to_list Sys.argv |> List.tl |> Option.value ~default:[] in
  let prog = Filename.basename Sys.argv.(0) in
  if List.mem "-h" args || List.mem "--help" args then (
    usage ();
    exit 0);
  if List.mem "--version" args then (
    version_info ();
    exit 0);
  let verbose = List.mem "-v" args || List.mem "--verbose" args in
  let flags = ["-v"; "--verbose"; "-q"; "--quiet"] in
  let files = List.filter (fun a -> not (List.mem a flags)) args in
  if verbose then Printf.eprintf "%s: verbose mode enabled\n" prog;
  copy_inputs files
