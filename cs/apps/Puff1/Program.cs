using Puff1;
using Puff1.Resources;
using static Puff1.Resources.I18n;

I18n.ApplyUserCulture();

static void Usage()
{
    Console.Out.Write(T("Help_Usage"));
    Console.Out.Write(T("Help_Concat"));
    Console.Out.Write(T("Help_ReadStdin"));
    Console.Out.Write("  -v, --verbose      ");
    Console.Out.Write(T("Option_Verbose"));
    Console.Out.Write("  -q, --quiet        ");
    Console.Out.Write(T("Option_Quiet"));
    Console.Out.Write("  -h, --help         ");
    Console.Out.Write(T("Option_Help"));
    Console.Out.Write("      --version      ");
    Console.Out.Write(T("Option_Version"));
    Console.Out.WriteLine(T("ReportBugs", BuildInfo.ProjectEmail));
}

static void VersionInfo()
{
    Console.Out.WriteLine(T("Version_Title"));
    Console.Out.WriteLine(T("Copyright", BuildInfo.ProjectYear, BuildInfo.ProjectAuthor));
    Console.Out.WriteLine(T("Version_License"));
    Console.Out.WriteLine(T("Version_FreeSoftware"));
    Console.Out.WriteLine(T("Version_OpposesAI"));
    Console.Out.WriteLine(T("Version_RejectsLicensing"));
    Console.Out.WriteLine(T("Version_NoWarranty"));
}

var argsList = args.ToList();
if (argsList.Contains("-h") || argsList.Contains("--help"))
{
    Usage();
    return 0;
}
if (argsList.Contains("--version"))
{
    VersionInfo();
    return 0;
}

var verbose = argsList.Contains("-v") || argsList.Contains("--verbose");
var files = argsList.Where(a => a is not "-v" and not "--verbose" and not "-q" and not "--quiet").ToList();
if (verbose)
{
    Console.Error.WriteLine($"{Environment.GetCommandLineArgs()[0]}: verbose mode enabled");
}

try
{
    if (files.Count == 0)
    {
        await common_lib.CopyStreamAsync(Console.OpenStandardInput(), Console.OpenStandardOutput());
        return 0;
    }

    foreach (var f in files)
    {
        if (f == "-")
        {
            await common_lib.CopyStreamAsync(Console.OpenStandardInput(), Console.OpenStandardOutput());
        }
        else
        {
            await common_lib.CopyFileAsync(f, Console.OpenStandardOutput());
        }
    }
}
catch (Exception e)
{
    Console.Error.WriteLine($"{Environment.GetCommandLineArgs()[0]}: {e.Message}");
    return 1;
}

return 0;
