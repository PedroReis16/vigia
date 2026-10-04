namespace Vigia.API.Config;

public class ClipOptions
{
    public const string SectionName = "Clips";

    public string StagingDirectory { get; set; } = string.Empty;

    public string FfmpegPath { get; set; } = "ffmpeg";

    public int SessionTtlMinutes { get; set; } = 15;
}
