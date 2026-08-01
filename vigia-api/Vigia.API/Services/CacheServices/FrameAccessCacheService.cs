using System.Security.Cryptography;
using Vigia.API.Contracts.CacheServices;
using Vigia.Cache.Services;

namespace Vigia.API.Services.CacheServices;

/// <summary>
/// Tokens de thumb reutilizáveis dentro do TTL (adequado a &lt;img&gt;).
/// Novas listagens reaproveitam o token vigente em vez de invalidá-lo.
/// </summary>
internal class FrameAccessCacheService(IRedisCacheService cacheService) : IFrameAccessCacheService
{
    /// <summary>Aligned with <see cref="DeviceFrameCacheService"/> frame TTL.</summary>
    private static readonly TimeSpan CacheTtl = TimeSpan.FromSeconds(120);

    private static string GetTokenCacheKey(string token) => $"frame-access-{token}";

    private static string GetOwnerCacheKey(Guid userId, Guid deviceId) =>
        $"frame-access-owner-{userId}-{deviceId}";

    public string IssueToken(Guid userId, Guid deviceId)
    {
        string ownerKey = GetOwnerCacheKey(userId, deviceId);

        string? existingToken = cacheService.Get<string>(ownerKey);
        if (!string.IsNullOrEmpty(existingToken))
        {
            FrameAccessTokenEntry? existing = cacheService.Get<FrameAccessTokenEntry>(
                GetTokenCacheKey(existingToken));

            if (existing is not null
                && existing.UserId == userId
                && existing.DeviceId == deviceId)
            {
                return existingToken;
            }
        }

        string token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant();
        FrameAccessTokenEntry entry = new(userId, deviceId);

        cacheService.Add(GetTokenCacheKey(token), entry, CacheTtl);
        cacheService.Add(ownerKey, token, CacheTtl);

        return token;
    }

    public FrameAccessTokenEntry? GetToken(string token)
    {
        if (string.IsNullOrWhiteSpace(token))
            return null;

        return cacheService.Get<FrameAccessTokenEntry>(GetTokenCacheKey(token));
    }
}
