namespace Vigia.API.Contracts.Devices;

public interface IVersionService
{
    Task UploadDeviceVersionAsync(string version, string filePath);

    Task<IReadOnlyList<string>> ListVersionsAsync();

    Task<string?> GetLatestVersionAsync();

    Task<Stream> DownloadVersionAsync(string version);
}
