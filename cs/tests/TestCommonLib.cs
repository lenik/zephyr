using System.Text;
using Puff1;

var input = new MemoryStream(Encoding.UTF8.GetBytes("alpha\nbeta\n"));
await using var output = new MemoryStream();
await common_lib.CopyStreamAsync(input, output);
var got = Encoding.UTF8.GetString(output.ToArray());
if (got != "alpha\nbeta\n")
{
    throw new Exception("CopyStreamAsync failed");
}
