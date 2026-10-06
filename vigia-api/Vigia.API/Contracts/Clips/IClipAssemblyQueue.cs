namespace Vigia.API.Contracts.Clips;

public sealed record ClipAssemblyJob(
    Guid DeviceId,
    Guid ClipId,
    int Fps,
    string StagingDirectory,
    int FrameCount);

public interface IClipAssemblyQueue
{
    void Enqueue(ClipAssemblyJob job);
}
