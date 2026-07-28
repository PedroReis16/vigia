using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.Primitives;
using Vigia.API.Contracts.CacheServices;
using Vigia.Cache.Config;
using Vigia.Cache.Services;

namespace Vigia.API.Services.CacheServices;

public class RevokedTokensCacheService(InMemoryCacheConfig config, IMemoryCache memoryCache) : InMemoryCacheService(config, memoryCache), IRevokedTokensCacheService
{
    private static string GetCacheKey(Guid tokenId) => $"revoked-tokens-{tokenId}";

    public string? GetToken(Guid tokenId) => Get(GetCacheKey(tokenId)) as string;


    public void SaveToken(Guid tokenId, DateTime expirationDate)
    {
        int expirationInSeconds = (int)Math.Max(0, (expirationDate - DateTime.UtcNow).TotalSeconds);

        MemoryCacheEntryOptions cacheEntryOptions = new MemoryCacheEntryOptions()
            .SetAbsoluteExpiration(TimeSpan.FromSeconds(expirationInSeconds));

        _ = cacheEntryOptions.AddExpirationToken(new CancellationChangeToken(ResetCacheSource.Token));

        _ = MemoryCache.Set(GetCacheKey(tokenId).ToUpperInvariant(), expirationInSeconds, cacheEntryOptions);
    }

}