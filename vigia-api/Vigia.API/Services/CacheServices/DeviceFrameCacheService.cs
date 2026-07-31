using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.Primitives;
using Vigia.API.Contracts.CacheServices;
using Vigia.Cache.Config;
using Vigia.Cache.Services;

namespace Vigia.API.Services.CacheServices;

internal class DeviceFrameCacheService(InMemoryCacheConfig config, IMemoryCache memoryCache) : InMemoryCacheService(config, memoryCache), IDeviceFrameCacheService
{
    private static string GetCacheKey(Guid deviceId) => $"device-frame-{deviceId}";

    public byte[]? GetFrame(Guid deviceId)
    {
        return Get(GetCacheKey(deviceId)) as byte[];
    }

    public void SetFrame(Guid deviceId, byte[] frame)
    {
        MemoryCacheEntryOptions cacheEntryOptions = new MemoryCacheEntryOptions()
            .SetAbsoluteExpiration(TimeSpan.FromSeconds(120));

        _ = cacheEntryOptions.AddExpirationToken(new CancellationChangeToken(ResetCacheSource.Token));

        _ = MemoryCache.Set(GetCacheKey(deviceId).ToUpperInvariant(), frame, cacheEntryOptions);
    }
}