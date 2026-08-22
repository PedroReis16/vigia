namespace Vigia.API.Contracts.Devices;

public sealed record DeviceUpdateInfo(string Revision, bool Available);

public interface IVersionService
{
    /// <summary>
    /// Sobrescreve o pacote OTA rolling e notifica devices via FIWARE.
    /// </summary>
    Task UploadDeviceUpdateAsync(string revision, string filePath);

    /// <summary>
    /// Metadados do pacote rolling atual, ou null se ainda não houver upload.
    /// </summary>
    Task<DeviceUpdateInfo?> GetCurrentUpdateAsync();

    /// <summary>
    /// Stream do pacote OTA rolling atual.
    /// </summary>
    Task<Stream> DownloadCurrentUpdateAsync();
}
