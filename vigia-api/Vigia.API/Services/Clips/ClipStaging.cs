using Vigia.API.Config;

namespace Vigia.API.Services.Clips;

internal static class ClipStaging
{
    public static string ResolveRoot(ClipOptions options)
    {
        if (!string.IsNullOrWhiteSpace(options.StagingDirectory))
            return options.StagingDirectory;

        return Path.Combine(Path.GetTempPath(), "vigia-clips");
    }

    public static string SessionDirectory(ClipOptions options, Guid deviceId, Guid clipId)
    {
        return Path.Combine(ResolveRoot(options), deviceId.ToString("D"), clipId.ToString("D"));
    }

    public static string FramePath(string sessionDirectory, int index)
    {
        return Path.Combine(sessionDirectory, $"{index:D6}.png");
    }

    public static bool HasAllFrames(string sessionDirectory, int frameCount)
    {
        for (int index = 0; index < frameCount; index++)
        {
            if (!File.Exists(FramePath(sessionDirectory, index)))
                return false;
        }

        return frameCount > 0;
    }

    public static void DeleteQuietly(string? path, ILogger logger)
    {
        if (string.IsNullOrWhiteSpace(path) || !Directory.Exists(path))
            return;

        try
        {
            Directory.Delete(path, recursive: true);
        }
        catch (Exception ex)
        {
            logger.LogWarning(ex, "Não foi possível apagar o staging {Path}", path);
        }
    }
}
