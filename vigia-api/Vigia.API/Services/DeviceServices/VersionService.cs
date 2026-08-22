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
    private const string OrionEntityPrefix = "urn:ngsi-ld:";
    private const int DevicesPageSize = 100;
    private const int MaxRetainedVersions = 5;

    private readonly ILogger<VersionService> _logger = logger;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    public async Task UploadDeviceVersionAsync(string version, string filePath)
    {
        try
        {
            using IServiceScope scope = _scopeFactory.CreateScope();
            ICloudService cloudService = scope.ServiceProvider.GetRequiredService<ICloudService>();
            IFiwareService fiwareService = scope.ServiceProvider.GetRequiredService<IFiwareService>();
            IConfiguration configuration = scope.ServiceProvider.GetRequiredService<IConfiguration>();

            string versionBucket = configuration.GetSection(CloudOptions.SectionName).Get<CloudOptions>()!.VersionsBucketName!;

            IReadOnlyList<string> existingKeys = await cloudService.ListKeysAsync(versionBucket);
            if (existingKeys.Contains(version, StringComparer.Ordinal))
            {
                throw new HttpResponseException(
                    StatusCodes.Status409Conflict,
                    $"A versão '{version}' já existe no repositório de versões.");
            }

            using FileStream fileStream = File.OpenRead(filePath);
            await cloudService.UploadFileAsync(versionBucket, version, fileStream, "application/gzip");

            await EnforceVersionRetentionAsync(cloudService, versionBucket);
            await BroadcastDeviceUpdateAsync(fiwareService, version);
        }
        catch (HttpResponseException)
        {
            throw;
        }
        catch (Exception ex)
        {
            string errorMessage = $"Error uploading device version: {ex.Message}";
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
                string errorMessage = $"Error deleting file: {ex.Message}";
                _logger.LogError(errorMessage);
            }
        }
    }

    public async Task<IReadOnlyList<string>> ListVersionsAsync()
    {
        using IServiceScope scope = _scopeFactory.CreateScope();
        ICloudService cloudService = scope.ServiceProvider.GetRequiredService<ICloudService>();
        IConfiguration configuration = scope.ServiceProvider.GetRequiredService<IConfiguration>();

        string versionBucket = configuration.GetSection(CloudOptions.SectionName).Get<CloudOptions>()!.VersionsBucketName!;
        IReadOnlyList<string> keys = await cloudService.ListKeysAsync(versionBucket);

        return keys
            .OrderByDescending(k => k, StringComparer.Ordinal)
            .ToList();
    }

    public async Task<string?> GetLatestVersionAsync()
    {
        IReadOnlyList<string> versions = await ListVersionsAsync();
        return SelectLatestSemVer(versions);
    }

    public async Task<Stream> DownloadVersionAsync(string version)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(version);

        using IServiceScope scope = _scopeFactory.CreateScope();
        ICloudService cloudService = scope.ServiceProvider.GetRequiredService<ICloudService>();
        IConfiguration configuration = scope.ServiceProvider.GetRequiredService<IConfiguration>();

        string versionBucket = configuration.GetSection(CloudOptions.SectionName).Get<CloudOptions>()!.VersionsBucketName!;

        try
        {
            return await cloudService.DownloadFileAsync(versionBucket, version);
        }
        catch (FileNotFoundException)
        {
            throw new HttpResponseException(
                StatusCodes.Status404NotFound,
                $"Versão '{version}' não encontrada.");
        }
    }

    private async Task EnforceVersionRetentionAsync(ICloudService cloudService, string versionBucket)
    {
        IReadOnlyList<string> keys = await cloudService.ListKeysAsync(versionBucket);
        IReadOnlyList<string> keysToDelete = SelectKeysToDelete(keys, MaxRetainedVersions);

        foreach (string key in keysToDelete)
        {
            try
            {
                await cloudService.DeleteFileAsync(versionBucket, key);
                _logger.LogInformation(
                    "Versão antiga removida por retenção (máx. {MaxRetained}): {Version}",
                    MaxRetainedVersions,
                    key);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(
                    ex,
                    "Falha ao remover versão antiga por retenção: {Version}",
                    key);
            }
        }
    }

    /// <summary>
    /// Seleciona as chaves mais antigas a remover para manter no máximo <paramref name="retainCount"/> objetos.
    /// Ordem (mais antiga primeiro): chaves não-SemVer; depois SemVer crescente; pré-releases antes de estáveis
    /// na mesma versão (alinhado a <see cref="SelectLatestSemVer"/>); desempate ordinal.
    /// </summary>
    internal static IReadOnlyList<string> SelectKeysToDelete(IEnumerable<string> keys, int retainCount)
    {
        List<string> keyList = keys.ToList();
        if (keyList.Count <= retainCount)
            return [];

        List<(string Key, Version? Version, bool IsPrerelease, bool Parsed)> items = [];
        foreach (string key in keyList)
        {
            if (TryParseSemVer(key, out Version version, out bool isPrerelease))
                items.Add((key, version, isPrerelease, true));
            else
                items.Add((key, null, false, false));
        }

        List<string> oldestFirst = items
            .OrderBy(i => i.Parsed)
            .ThenBy(i => i.Version ?? new Version(0, 0))
            .ThenByDescending(i => i.IsPrerelease)
            .ThenBy(i => i.Key, StringComparer.Ordinal)
            .Select(i => i.Key)
            .ToList();

        int deleteCount = keyList.Count - retainCount;
        return oldestFirst.Take(deleteCount).ToList();
    }

    private async Task BroadcastDeviceUpdateAsync(IFiwareService fiwareService, string version)
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
                        version);

                    if (sent)
                        notified++;
                    else
                    {
                        failed++;
                        _logger.LogWarning(
                            "Falha ao enviar device_update para {DeviceName} (versão {Version})",
                            deviceName,
                            version);
                    }
                }
                catch (Exception ex)
                {
                    failed++;
                    _logger.LogWarning(
                        ex,
                        "Erro ao enviar device_update para {DeviceName} (versão {Version})",
                        deviceName,
                        version);
                }
            }

            offset += devices.Count;

            if (devices.Count < DevicesPageSize || offset >= totalCount)
                break;
        }

        _logger.LogInformation(
            "Broadcast device_update concluído para versão {Version}. Notificados={Notified} Falhas={Failed}",
            version,
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

    internal static string? SelectLatestSemVer(IEnumerable<string> versions)
    {
        List<(string Original, Version Version, bool IsPrerelease)> parsed = [];

        foreach (string key in versions)
        {
            if (!TryParseSemVer(key, out Version version, out bool isPrerelease))
                continue;

            parsed.Add((key, version, isPrerelease));
        }

        if (parsed.Count == 0)
            return null;

        IEnumerable<(string Original, Version Version, bool IsPrerelease)> candidates =
            parsed.Exists(p => !p.IsPrerelease)
                ? parsed.Where(p => !p.IsPrerelease)
                : parsed;

        return candidates
            .OrderByDescending(p => p.Version)
            .ThenByDescending(p => p.Original, StringComparer.Ordinal)
            .First()
            .Original;
    }

    private static bool TryParseSemVer(string value, out Version version, out bool isPrerelease)
    {
        version = null!;
        isPrerelease = false;

        if (string.IsNullOrWhiteSpace(value))
            return false;

        string core = value;
        int dashIndex = value.IndexOf('-');
        if (dashIndex >= 0)
        {
            isPrerelease = true;
            core = value[..dashIndex];
        }

        if (!core.Contains('.'))
            core = $"{core}.0";

        return Version.TryParse(core, out version!);
    }
}
