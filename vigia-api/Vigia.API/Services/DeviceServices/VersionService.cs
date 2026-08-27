using System.Text;
using System.Text.Json;
using Vigia.API.Contracts.Devices;
using Vigia.Cloud.Config;
using Vigia.Cloud.Contracts;
using Vigia.Fiware.Contracts;
using Vigia.Fiware.Models.DeviceDTOs;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.Services.Devices;

internal class VersionService(ILogger<VersionService> logger, IServiceScopeFactory scopeFactory) : IVersionService
{
    /// <summary>Chave fixa do pacote OTA rolling (mesmo nome da tag GitHub).</summary>
    internal const string PackageObjectKey = "onboard";

    internal const string MetaObjectKey = "onboard.meta.json";

    private const string OrionEntityPrefix = "urn:ngsi-ld:";
    private const int DevicesPageSize = 100;

    private static readonly JsonSerializerOptions MetaJsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        PropertyNameCaseInsensitive = true,
        WriteIndented = false,
    };

    private readonly ILogger<VersionService> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    public async Task UploadDeviceUpdateAsync(string revision, string filePath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(revision);

        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();
            ICloudService cloudService = scope.ServiceProvider.GetRequiredService<ICloudService>();
            IFiwareService fiwareService = scope.ServiceProvider.GetRequiredService<IFiwareService>();
            IConfiguration configuration = scope.ServiceProvider.GetRequiredService<IConfiguration>();

            string versionBucket = configuration.GetSection(CloudOptions.SectionName).Get<CloudOptions>()!.VersionsBucketName!;

            using (FileStream fileStream = File.OpenRead(filePath))
            {
                await cloudService.UploadFileAsync(
                    versionBucket,
                    PackageObjectKey,
                    fileStream,
                    "application/gzip");
            }

            DeviceUpdateMeta meta = new(revision.Trim(), DateTimeOffset.UtcNow);
            await UploadMetaAsync(cloudService, versionBucket, meta);
            await RemoveLegacyObjectsAsync(cloudService, versionBucket);
            await BroadcastDeviceUpdateAsync(fiwareService, meta.Revision);
        }
        catch (HttpResponseException)
        {
            throw;
        }
        catch (Exception ex)
        {
            string errorMessage = $"Error uploading device update: {ex.Message}";
            _logger.LogError(errorMessage);
            throw new Exception(errorMessage, ex);
        }
        finally
        {
            try
            {
                File.Delete(filePath);
            }
            catch (Exception ex)
            {
                _logger.LogError("Error deleting staging file: {Message}", ex.Message);
            }
        }
    }

    public async Task<DeviceUpdateInfo?> GetCurrentUpdateAsync()
    {
        using IServiceScope scope = _scopeFactory.CreateScope();
        ICloudService cloudService = scope.ServiceProvider.GetRequiredService<ICloudService>();
        IConfiguration configuration = scope.ServiceProvider.GetRequiredService<IConfiguration>();

        string versionBucket = configuration.GetSection(CloudOptions.SectionName).Get<CloudOptions>()!.VersionsBucketName!;
        IReadOnlyList<string> keys = await cloudService.ListKeysAsync(versionBucket);

        if (!keys.Contains(PackageObjectKey, StringComparer.Ordinal))
            return null;

        DeviceUpdateMeta? meta = await TryReadMetaAsync(cloudService, versionBucket);
        string revision = meta?.Revision?.Trim() ?? PackageObjectKey;
        if (string.IsNullOrWhiteSpace(revision))
            revision = PackageObjectKey;

        return new DeviceUpdateInfo(revision, Available: true);
    }

    public async Task<Stream> DownloadCurrentUpdateAsync()
    {
        using IServiceScope scope = _scopeFactory.CreateScope();
        ICloudService cloudService = scope.ServiceProvider.GetRequiredService<ICloudService>();
        IConfiguration configuration = scope.ServiceProvider.GetRequiredService<IConfiguration>();

        string versionBucket = configuration.GetSection(CloudOptions.SectionName).Get<CloudOptions>()!.VersionsBucketName!;

        try
        {
            return await cloudService.DownloadFileAsync(versionBucket, PackageObjectKey);
        }
        catch (FileNotFoundException)
        {
            throw new HttpResponseException(
                StatusCodes.Status404NotFound,
                "Nenhum pacote OTA disponível.");
        }
    }

    private async Task UploadMetaAsync(ICloudService cloudService, string bucket, DeviceUpdateMeta meta)
    {
        byte[] bytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(meta, MetaJsonOptions));
        using MemoryStream stream = new(bytes);
        await cloudService.UploadFileAsync(bucket, MetaObjectKey, stream, "application/json");
    }

    private async Task<DeviceUpdateMeta?> TryReadMetaAsync(ICloudService cloudService, string bucket)
    {
        try
        {
            await using Stream stream = await cloudService.DownloadFileAsync(bucket, MetaObjectKey);
            using MemoryStream buffer = new();
            await stream.CopyToAsync(buffer);
            return JsonSerializer.Deserialize<DeviceUpdateMeta>(buffer.ToArray(), MetaJsonOptions);
        }
        catch (FileNotFoundException)
        {
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Falha ao ler metadados OTA ({MetaKey})", MetaObjectKey);
            return null;
        }
    }

    /// <summary>
    /// Remove chaves antigas do modelo multi-versão, mantendo só o pacote rolling + meta.
    /// </summary>
    private async Task RemoveLegacyObjectsAsync(ICloudService cloudService, string bucket)
    {
        IReadOnlyList<string> keys = await cloudService.ListKeysAsync(bucket);
        foreach (string key in keys)
        {
            if (string.Equals(key, PackageObjectKey, StringComparison.Ordinal) ||
                string.Equals(key, MetaObjectKey, StringComparison.Ordinal))
            {
                continue;
            }

            try
            {
                await cloudService.DeleteFileAsync(bucket, key);
                _logger.LogInformation("Objeto OTA legado removido: {Key}", key);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Falha ao remover objeto OTA legado: {Key}", key);
            }
        }
    }

    private async Task BroadcastDeviceUpdateAsync(IFiwareService fiwareService, string revision)
    {
        int offset = 0;
        int notified = 0;
        int failed = 0;

        while (true)
        {
            (List<IotAgentDeviceDTO> devices, int totalCount) =
                await fiwareService.ListDevicesPageAsync(offset, DevicesPageSize);

            if (devices.Count == 0)
                break;

            foreach (IotAgentDeviceDTO device in devices)
            {
                string? deviceName = ExtractDeviceName(device.EntityName);
                if (string.IsNullOrWhiteSpace(deviceName))
                {
                    _logger.LogWarning(
                        "Ignorando device IoT Agent sem entity_name válida. DeviceId={DeviceId}",
                        device.DeviceId);
                    continue;
                }

                try
                {
                    bool sent = await fiwareService.SendCommandAsync(
                        deviceName,
                        DeviceCommands.DEVICE_UPDATE,
                        revision);

                    if (sent)
                        notified++;
                    else
                    {
                        failed++;
                        _logger.LogWarning(
                            "Falha ao enviar device_update para {DeviceName} (revision {Revision})",
                            deviceName,
                            revision);
                    }
                }
                catch (Exception ex)
                {
                    failed++;
                    _logger.LogWarning(
                        ex,
                        "Erro ao enviar device_update para {DeviceName} (revision {Revision})",
                        deviceName,
                        revision);
                }
            }

            offset += devices.Count;

            if (devices.Count < DevicesPageSize || offset >= totalCount)
                break;
        }

        _logger.LogInformation(
            "Broadcast device_update concluído para revision {Revision}. Notificados={Notified} Falhas={Failed}",
            revision,
            notified,
            failed);
    }

    private static string? ExtractDeviceName(string? entityName)
    {
        if (string.IsNullOrWhiteSpace(entityName))
            return null;

        if (entityName.StartsWith(OrionEntityPrefix, StringComparison.OrdinalIgnoreCase))
            return entityName[OrionEntityPrefix.Length..];

        return entityName;
    }

    private sealed record DeviceUpdateMeta(string Revision, DateTimeOffset UploadedAt);
}
