defmodule TestCommons do
  use ExUnit.Case, async: true

  test "write and read roundtrip" do
    tmp = Path.join(System.tmp_dir!(), "commons-test-input.txt")
    content = "alpha\nbeta\n"
    :ok = File.write(tmp, content)
    assert File.read!(tmp) == content
    :ok = File.rm(tmp)
  end
end

ExUnit.start()
