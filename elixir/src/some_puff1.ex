defmodule SomePuff1 do
  @moduledoc false

  defp tr(s), do: s

  defp usage do
    IO.puts(tr("Usage: some_puff1 [OPTION]... [FILE]..."))
    IO.puts(tr("Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,"))
    IO.puts(tr("read standard input.\n"))
    IO.puts("  -v, --verbose      " <> tr("repeat for more verbose loggings"))
    IO.puts("  -q, --quiet        " <> tr("show less logging messages"))
    IO.puts("  -h, --help         " <> tr("display this help and exit"))
    IO.puts("      --version      " <> tr("output version information and exit\n"))
    IO.puts(tr("Report bugs to: <zephyr@bodz.net>"))
  end

  defp version_info do
    IO.puts("some_puff1 dev")
    IO.puts(tr("Copyright (C) 2026 Lenik"))
    IO.puts(tr("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>"))
    IO.puts(tr("This is free software: you are free to change and redistribute it."))
    IO.puts(tr("This project opposes AI exploitation and AI hegemony."))
    IO.puts(tr("This project rejects mindless MIT-style licensing and politically naive BSD-style licensing."))
    IO.puts(tr("There is NO WARRANTY, to the extent permitted by law."))
  end

  defp copy_files([]), do: :ok

  defp copy_files(["-" | rest]) do
    case Commons.copy_stream(:standard_io, :standard_io) do
      :ok -> copy_files(rest)
      {:error, reason} -> {:error, reason}
    end
  end

  defp copy_files([file | rest]) do
    case Commons.copy_file(file) do
      :ok -> copy_files(rest)
      {:error, reason} -> {:error, {file, reason}}
    end
  end

  def main(argv) do
    cond do
      "-h" in argv or "--help" in argv ->
        usage()
        System.halt(0)

      "--version" in argv ->
        version_info()
        System.halt(0)

      true ->
        verbose = "-v" in argv or "--verbose" in argv
        flags = ["-v", "--verbose", "-q", "--quiet"]
        files = Enum.reject(argv, &(&1 in flags))

        if verbose do
          IO.puts(:standard_error, "some_puff1: verbose mode enabled")
        end

        result =
          case files do
            [] -> Commons.copy_stream(:standard_io, :standard_io)
            _ -> copy_files(files)
          end

        case result do
          :ok ->
            System.halt(0)

          {:error, {file, reason}} ->
            IO.puts(:standard_error, "some_puff1: #{file}: #{inspect(reason)}")
            System.halt(1)

          {:error, reason} ->
            IO.puts(:standard_error, "some_puff1: #{inspect(reason)}")
            System.halt(1)
        end
    end
  end
end
