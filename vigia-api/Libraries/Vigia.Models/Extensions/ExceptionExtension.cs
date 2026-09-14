using System.Text;

namespace Vigia.Models.Extensions;

public static class ExceptionExtension
{
    public static string GetFullMessage(this Exception ex)
    {
        StringBuilder sb = new();
        _ = sb.AppendLine(ex.Message);
        if (ex.InnerException != null)
            _ = sb.AppendLine(GetFullMessage(ex.InnerException));
        return sb.ToString();
    }
}