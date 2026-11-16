namespace Vigia.API.Contracts.Clips;

public interface IClipAssembler
{
    Task AssembleAsync(string framesDirectory, int fps, string outputPath, CancellationToken cancellationToken = default);

    Task WritePosterAsync(string sourceFramePath, string outputPath, CancellationToken cancellationToken = default);

    Task WritePosterFromVideoAsync(string videoPath, string outputPath, CancellationToken cancellationToken = default);
}
