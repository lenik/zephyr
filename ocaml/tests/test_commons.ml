let () =
  let tmp_in = Filename.temp_file "some_puff1-in" ".txt" in
  let tmp_out = Filename.temp_file "some_puff1-out" ".txt" in
  let oc = open_out tmp_in in
  output_string oc "alpha\nbeta\n";
  close_out oc;
  let out = open_out_bin tmp_out in
  Commons.copy_file_to tmp_in out;
  close_out out;
  let ic = open_in tmp_out in
  let got = really_input_string ic (in_channel_length ic) in
  close_in ic;
  if got <> "alpha\nbeta\n" then failwith "copy_file_to failed";
  Sys.remove tmp_in;
  Sys.remove tmp_out
