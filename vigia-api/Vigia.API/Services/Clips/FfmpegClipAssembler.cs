using System.Diagnostics;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts.Clips;

namespace Vigia.API.Services.Clips;

internal sealed class FfmpegClipAssembler(IOptions<ClipOptions> options, ILogger<FfmpegClipAssembler> logger) : IClipAssembler
{
    private readonly ClipOptions _options = options.Value;
    private readonly ILogger<FfmpegClipAssembler> _logger = logger;

    public Task AssembleAsync(string framesDirectory, int fps, string outputPath, CancellationToken cancellationToken = default)
    {
        string pattern = Path.Combine(framesDirectory, "%06d.png");
        return RunAsync(
            [
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                Math.Max(1, fps).ToString(),
                "-start_number",
                "0",
                "-i",
                pattern,
                "-c:v",
                "libx264",
                "-crf",
                "18",
                "-preset",
                "slow",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                outputPath,
            ],
            cancellationToken);
    }

    public Task WritePosterAsync(string sourceFramePath, string outputPath, CancellationToken cancellationToken = default)
    {
        return RunAsync(
            [
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                sourceFramePath,
                "-frames:v",
                "1",
                "-vf",
                "scale='min(480,iw)':-2",
                "-q:v",
                "5",
                outputPath,
            ],
            cancellationToken);
    }

    public Task WritePosterFromVideoAsync(string videoPath, string outputPath, CancellationToken cancellationToken = default)
    {
        return RunAsync(
            [
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                "0",
                "-i",
                videoPath,
                "-frames:v",
                "1",
                "-vf",
                "scale='min(480,iw)':-2",
                "-q:v",
                "5",
                outputPath,
            ],
            cancellationToken);
    }

    private async Task RunAsync(IReadOnlyList<string> arguments, CancellationToken cancellationToken)
    {
        string ffmpeg = string.IsNullOrWhiteSpace(_options.FfmpegPath) ? "ffmpeg" : _options.FfmpegPath;
        ProcessStartInfo startInfo = new()
        {
            FileName = ffmpeg,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };

        foreach (string argument in arguments)
            startInfo.ArgumentList.Add(argument);

        using Process process = new() { StartInfo = startInfo };
        if (!process.Start())
            throw new InvalidOperationException($"Não foi possível iniciar {ffmpeg}");

        Task<string> stderrTask = process.StandardError.ReadToEndAsync(cancellationToken);
        await process.WaitForExitAsync(cancellationToken);
        string stderr = await stderrTask;

        if (process.ExitCode != 0)
        {
            _logger.LogError("ffmpeg falhou ({ExitCode}): {Error}", process.ExitCode, stderr);
            throw new InvalidOperationException($"ffmpeg saiu com código {process.ExitCode}");
        }
    }
}
