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

    public static async Task<string> WritePartialAsync(
        string sessionDirectory,
        int index,
        byte[] bytes,
        CancellationToken cancellationToken)
    {
        Directory.CreateDirectory(sessionDirectory);
        string partial = Path.Combine(sessionDirectory, $"{index:D6}.{Guid.NewGuid():N}.partial");
        await File.WriteAllBytesAsync(partial, bytes, cancellationToken);
        return partial;
    }

    public static void CommitFrame(string partialPath, string framePath)
    {
        File.Move(partialPath, framePath, overwrite: true);
    }

    public static void DeleteFileQuietly(string? path)
    {
        if (string.IsNullOrWhiteSpace(path) || !File.Exists(path))
            return;

        try
        {
            File.Delete(path);
        }
        catch (IOException)
        {
        }
        catch (UnauthorizedAccessException)
        {
        }
    }

    /// <summary>
    /// Copia os frames 0..frameCount-1 para uma pasta ordenada, independente da ordem de chegada.
    /// </summary>
    public static string ArrangeSequence(string sessionDirectory, int frameCount)
    {
        if (!HasAllFrames(sessionDirectory, frameCount))
            throw new InvalidOperationException("A sequência de frames está incompleta");

        string ordered = Path.Combine(sessionDirectory, "ordered");
        if (Directory.Exists(ordered))
            Directory.Delete(ordered, recursive: true);

        Directory.CreateDirectory(ordered);
        for (int index = 0; index < frameCount; index++)
        {
            File.Copy(
                FramePath(sessionDirectory, index),
                Path.Combine(ordered, $"{index:D6}.png"),
                overwrite: true);
        }

        return ordered;
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
