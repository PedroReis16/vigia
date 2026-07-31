using Vigia.API.Contracts.CacheServices;
using Vigia.Database.Contracts;
using Vigia.Models.Contracts;
using Vigia.Models.Entities;

namespace Vigia.API.Services;

internal class DeviceSignPublicKeyProvider(
    IDeviceIdentityCacheService identityCache,
    IServiceScopeFactory scopeFactory) : IDeviceSignPublicKeyProvider
{
    public async Task<string?> GetSignPublicKeyAsync(Guid deviceId)
    {
        string? cached = identityCache.GetSignPublicKey(deviceId);
        if (!string.IsNullOrEmpty(cached))
            return cached;

        using IServiceScope scope = scopeFactory.CreateScope();
        IDevicesDao devicesDao = scope.ServiceProvider.GetRequiredService<IDevicesDao>();
        Device? device = await devicesDao.FindAsync(deviceId);

        if (device == null || string.IsNullOrWhiteSpace(device.SignPublicKey))
            return null;

        identityCache.SetSignPublicKey(deviceId, device.SignPublicKey);
        return device.SignPublicKey;
    }

    public void SetSignPublicKey(Guid deviceId, string signPublicKey)
    {
        identityCache.SetSignPublicKey(deviceId, signPublicKey);
    }
}
