let copy_handle_to input output =
  let buf = Bytes.create 8192 in
  let rec loop () =
    let n = input_binary_chan input buf 0 (Bytes.length buf) in
    if n = 0 then ()
    else (
      output_binary output buf 0 n;
      flush output;
      loop ())
  in
  loop ()

let copy_file_to path output =
  let input = open_in_bin path in
  Fun.protect
    ~finally:(fun () -> close_in input)
    (fun () -> copy_handle_to input output)
