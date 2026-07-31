using System.Security.Cryptography;
using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.Primitives;
using Vigia.API.Contracts.CacheServices;
using Vigia.Cache.Config;
using Vigia.Cache.Services;

namespace Vigia.API.Services.CacheServices;

/// <summary>
/// Tokens de thumb reutilizáveis dentro do TTL (adequado a &lt;img&gt;).
/// Nova listagem rotaciona o token do par user+device e invalida o anterior.
/// </summary>
internal class FrameAccessCacheService(InMemoryCacheConfig config, IMemoryCache memoryCache)
    : InMemoryCacheService(config, memoryCache), IFrameAccessCacheService
{
    private static readonly TimeSpan CacheTtl = TimeSpan.FromSeconds(90);

    private static string GetTokenCacheKey(string token) => $"frame-access-{token}";

    private static string GetOwnerCacheKey(Guid userId, Guid deviceId) =>
        $"frame-access-owner-{userId}-{deviceId}";

    public string IssueToken(Guid userId, Guid deviceId)
    {
        string ownerKey = GetOwnerCacheKey(userId, deviceId);

        if (Get(ownerKey) is string previousToken)
            Remove(GetTokenCacheKey(previousToken));

        string token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant();
        FrameAccessTokenEntry entry = new(userId, deviceId);

        MemoryCacheEntryOptions cacheEntryOptions = new MemoryCacheEntryOptions()
            .SetAbsoluteExpiration(CacheTtl);

        _ = cacheEntryOptions.AddExpirationToken(new CancellationChangeToken(ResetCacheSource.Token));

        string tokenKey = GetTokenCacheKey(token).ToUpperInvariant();
        string ownerKeyNormalized = ownerKey.ToUpperInvariant();

        _ = MemoryCache.Set(tokenKey, entry, cacheEntryOptions);
        _ = MemoryCache.Set(ownerKeyNormalized, token, cacheEntryOptions);

        return token;
    }

    public FrameAccessTokenEntry? GetToken(string token)
    {
        if (string.IsNullOrWhiteSpace(token))
            return null;

        return Get(GetTokenCacheKey(token)) as FrameAccessTokenEntry;
    }
}
