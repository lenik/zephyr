using System.Globalization;
using System.Resources;

namespace Puff1.Resources;

internal static class I18n
{
    private static readonly ResourceManager Rm = new("Puff1.Resources.Strings", typeof(I18n).Assembly);
    private static CultureInfo? _userCulture;

    internal static void ApplyUserCulture()
    {
        _userCulture = CultureFromEnv();
        if (_userCulture is not null)
        {
            CultureInfo.DefaultThreadCurrentUICulture = _userCulture;
            Thread.CurrentThread.CurrentUICulture = _userCulture;
            Thread.CurrentThread.CurrentCulture = _userCulture;
        }
    }

    private static CultureInfo? CultureFromEnv()
    {
        var raw = Environment.GetEnvironmentVariable("LC_ALL")
            ?? Environment.GetEnvironmentVariable("LC_MESSAGES")
            ?? Environment.GetEnvironmentVariable("LANG");
        if (string.IsNullOrWhiteSpace(raw) || raw is "C" or "POSIX")
        {
            return null;
        }

        var s = raw.Split('.')[0].Trim().Replace('_', '-');
        try
        {
            return CultureInfo.GetCultureInfo(s);
        }
        catch (CultureNotFoundException)
        {
            return null;
        }
    }

    internal static string T(string name, params object?[] args)
    {
        var c = _userCulture ?? CultureInfo.CurrentUICulture;
        var template = Rm.GetString(name, c) ?? Rm.GetString(name, CultureInfo.InvariantCulture);
        if (template is null)
        {
            return name;
        }

        if (args is { Length: > 0 })
        {
            return string.Format(c, template, args);
        }

        return template;
    }
}
