using System.Diagnostics;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Contracts.Clips;

namespace Vigia.API.Services.Clips;

internal sealed class FfmpegClipAssembler(IOptions<ClipOptions> options, ILogger<FfmpegClipAssembler> logger) : IClipAssembler
{
    private readonly ClipOptions _options = options.Value;
    private readonly ILogger<FfmpegClipAssembler> _logger = logger;

    public async Task AssembleAsync(string framesDirectory, int fps, string outputPath, CancellationToken cancellationToken = default)
    {
        string ffmpeg = string.IsNullOrWhiteSpace(_options.FfmpegPath) ? "ffmpeg" : _options.FfmpegPath;
        string pattern = Path.Combine(framesDirectory, "%06d.png");

        ProcessStartInfo startInfo = new()
        {
            FileName = ffmpeg,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };

        startInfo.ArgumentList.Add("-y");
        startInfo.ArgumentList.Add("-hide_banner");
        startInfo.ArgumentList.Add("-loglevel");
        startInfo.ArgumentList.Add("error");
        startInfo.ArgumentList.Add("-framerate");
        startInfo.ArgumentList.Add(Math.Max(1, fps).ToString());
        startInfo.ArgumentList.Add("-start_number");
        startInfo.ArgumentList.Add("0");
        startInfo.ArgumentList.Add("-i");
        startInfo.ArgumentList.Add(pattern);
        startInfo.ArgumentList.Add("-c:v");
        startInfo.ArgumentList.Add("libx264");
        startInfo.ArgumentList.Add("-crf");
        startInfo.ArgumentList.Add("18");
        startInfo.ArgumentList.Add("-preset");
        startInfo.ArgumentList.Add("slow");
        startInfo.ArgumentList.Add("-pix_fmt");
        startInfo.ArgumentList.Add("yuv420p");
        startInfo.ArgumentList.Add("-movflags");
        startInfo.ArgumentList.Add("+faststart");
        startInfo.ArgumentList.Add(outputPath);

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
