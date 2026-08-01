using Vigia.API.Contracts.CacheServices;
using Vigia.Cache.Services;

namespace Vigia.API.Services.CacheServices;

internal class DeviceIdentityCacheService(IRedisCacheService cacheService) : IDeviceIdentityCacheService
{
    private static readonly TimeSpan CacheTtl = TimeSpan.FromHours(24);

    private static string GetCacheKey(Guid deviceId) => $"device-sign-pub-{deviceId}";

    public string? GetSignPublicKey(Guid deviceId) =>
        cacheService.Get<string>(GetCacheKey(deviceId));

    public void SetSignPublicKey(Guid deviceId, string signPublicKey) =>
        cacheService.Add(GetCacheKey(deviceId), signPublicKey, CacheTtl);
}
