namespace Vigia.API.Contracts.Clips;

public interface IClipAssembler
{
    Task AssembleAsync(string framesDirectory, int fps, string outputPath, CancellationToken cancellationToken = default);
}
