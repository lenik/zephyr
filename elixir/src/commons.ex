defmodule Commons do
  @moduledoc false

  def copy_stream(in_device, out_device) do
    copy_loop(in_device, out_device)
  end

  defp copy_loop(in_device, out_device) do
    case :file.read(in_device, 65_536) do
      :eof ->
        :ok

      {:ok, bin} ->
        :ok = :file.write(out_device, bin)
        copy_loop(in_device, out_device)

      {:error, reason} ->
        {:error, reason}
    end
  end

  def copy_file(path) do
    case File.open(path, [:read, :binary]) do
      {:ok, in_device} ->
        result = copy_stream(in_device, :standard_io)
        File.close(in_device)
        result

      {:error, reason} ->
        {:error, reason}
    end
  end
end
