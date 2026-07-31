using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.Primitives;
using Vigia.API.Contracts.CacheServices;
using Vigia.Cache.Config;
using Vigia.Cache.Services;

namespace Vigia.API.Services.CacheServices;

internal class DeviceIdentityCacheService(InMemoryCacheConfig config, IMemoryCache memoryCache)
    : InMemoryCacheService(config, memoryCache), IDeviceIdentityCacheService
{
    private static readonly TimeSpan CacheTtl = TimeSpan.FromHours(24);

    private static string GetCacheKey(Guid deviceId) => $"device-sign-pub-{deviceId}";

    public string? GetSignPublicKey(Guid deviceId)
    {
        return Get(GetCacheKey(deviceId)) as string;
    }

    public void SetSignPublicKey(Guid deviceId, string signPublicKey)
    {
        MemoryCacheEntryOptions cacheEntryOptions = new MemoryCacheEntryOptions()
            .SetAbsoluteExpiration(CacheTtl);

        _ = cacheEntryOptions.AddExpirationToken(new CancellationChangeToken(ResetCacheSource.Token));

        _ = MemoryCache.Set(GetCacheKey(deviceId).ToUpperInvariant(), signPublicKey, cacheEntryOptions);
    }
}
