using System.IO;
using System.Threading.Tasks;

namespace Puff1;

public static class common_lib
{
    public static async Task CopyStreamAsync(Stream input, Stream output)
    {
        await input.CopyToAsync(output);
    }

    public static async Task CopyFileAsync(string path, Stream output)
    {
        await using var fs = File.OpenRead(path);
        await CopyStreamAsync(fs, output);
    }
}
