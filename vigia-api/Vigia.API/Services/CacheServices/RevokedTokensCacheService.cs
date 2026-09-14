using Vigia.API.Contracts.CacheServices;
using Vigia.Cache.Services;

namespace Vigia.API.Services.CacheServices;

public class RevokedTokensCacheService(IRedisCacheService cacheService) : IRevokedTokensCacheService
{
    private static string GetCacheKey(Guid tokenId) => $"revoked-tokens-{tokenId}";

    public string? GetToken(Guid tokenId) => cacheService.Get<string>(GetCacheKey(tokenId));

    public void SaveToken(Guid tokenId, DateTime expirationDate)
    {
        int expirationInSeconds = (int)Math.Max(0, (expirationDate - DateTime.UtcNow).TotalSeconds);
        cacheService.Add(GetCacheKey(tokenId), tokenId.ToString(), TimeSpan.FromSeconds(expirationInSeconds));
    }
}
