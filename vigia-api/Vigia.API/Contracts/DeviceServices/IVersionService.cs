namespace Vigia.API.Contracts.Devices;

public interface IVersionService
{
    Task UploadDeviceVersionAsync(string version, string filePath);
}
