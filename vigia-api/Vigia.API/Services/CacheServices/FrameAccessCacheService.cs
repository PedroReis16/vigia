using System.Security.Cryptography;
using Vigia.API.Contracts.CacheServices;
using Vigia.Cache.Services;

namespace Vigia.API.Services.CacheServices;

/// <summary>
/// Tokens de thumb reutilizáveis dentro do TTL (adequado a &lt;img&gt;).
/// Listagens reaproveitam e renovam o token vigente — nunca o invalidam/consomem.
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
            string tokenKey = GetTokenCacheKey(existingToken);
            FrameAccessTokenEntry? existing = cacheService.Get<FrameAccessTokenEntry>(tokenKey);

            if (existing is not null
                && existing.UserId == userId
                && existing.DeviceId == deviceId)
            {
                // Sliding TTL: listing must not let the token die while the frame is still cached.
                cacheService.Add(tokenKey, existing, CacheTtl);
                cacheService.Add(ownerKey, existingToken, CacheTtl);
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

        // Read-only validation — never delete/consume the token on image fetch.
        return cacheService.Get<FrameAccessTokenEntry>(GetTokenCacheKey(token));
    }
}
