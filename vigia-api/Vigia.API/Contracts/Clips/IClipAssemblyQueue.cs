namespace Vigia.API.Contracts.Clips;

public sealed record ClipAssemblyJob(Guid DeviceId, Guid ClipId, int Fps, string StagingDirectory);

public interface IClipAssemblyQueue
{
    void Enqueue(ClipAssemblyJob job);
}
