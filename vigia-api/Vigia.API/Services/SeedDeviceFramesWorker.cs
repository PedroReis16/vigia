#if DEBUG
using Vigia.API.Contracts.CacheServices;
using Vigia.API.Seed;

namespace Vigia.API.Services;

/// <summary>
/// Em DEBUG, garante thumbnail no Redis para o pool mock quando offline.
/// Não sobrescreve frames já presentes (ex.: worker a enviar JPEG).
/// </summary>
internal sealed class SeedDeviceFramesWorker(
    IDeviceFrameCacheService frameCache,
    ILogger<SeedDeviceFramesWorker> logger) : BackgroundService
{
    private static readonly TimeSpan RefreshInterval = TimeSpan.FromSeconds(60);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        logger.LogInformation(
            "Seed de thumbnails DEBUG ativo ({Count} JPEGs embutidos)",
            SeedDeviceFrameCatalog.All.Count);

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                EnsureMissingFrames();
            }
            catch (Exception ex)
            {
                logger.LogWarning(ex, "Falha ao seedar thumbnails DEBUG");
            }

            try
            {
                await Task.Delay(RefreshInterval, stoppingToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }
        }
    }

    private void EnsureMissingFrames()
    {
        int seeded = 0;
        foreach (Guid deviceId in SeedDeviceFrameCatalog.DeviceIds)
        {
            if (frameCache.HasFrame(deviceId))
                continue;

            if (!SeedDeviceFrameCatalog.TryGet(deviceId, out byte[] jpeg))
            {
                logger.LogWarning("JPEG seed ausente para device {DeviceId}", deviceId);
                continue;
            }

            frameCache.SetFrame(deviceId, jpeg);
            seeded++;
        }

        if (seeded > 0)
            logger.LogInformation("Thumbnails seed aplicadas a {Count} device(s)", seeded);
    }
}
#endif
