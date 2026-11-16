using System.Security.Cryptography;
using Vigia.API.Contracts.CacheServices;
using Vigia.Cache.Services;

namespace Vigia.API.Services.CacheServices;

/// <summary>
/// Tokens de mídia de clipe reutilizáveis dentro do TTL (adequado a img e video).
/// A validação renova o prazo para a reprodução não expirar no meio do playback.
/// </summary>
internal class ClipAccessCacheService(IRedisCacheService cacheService) : IClipAccessCacheService
{
    private static readonly TimeSpan CacheTtl = TimeSpan.FromHours(1);

    private static string GetTokenCacheKey(string token) => $"clip-access-{token}";

    private static string GetOwnerCacheKey(Guid userId, Guid deviceId) =>
        $"clip-access-owner-{userId}-{deviceId}";

    public string IssueToken(Guid userId, Guid deviceId)
    {
        string ownerKey = GetOwnerCacheKey(userId, deviceId);

        string? existingToken = cacheService.Get<string>(ownerKey);
        if (!string.IsNullOrEmpty(existingToken))
        {
            string tokenKey = GetTokenCacheKey(existingToken);
            ClipAccessTokenEntry? existing = cacheService.Get<ClipAccessTokenEntry>(tokenKey);

            if (existing is not null
                && existing.UserId == userId
                && existing.DeviceId == deviceId)
            {
                cacheService.Add(tokenKey, existing, CacheTtl);
                cacheService.Add(ownerKey, existingToken, CacheTtl);
                return existingToken;
            }
        }

        string token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant();
        ClipAccessTokenEntry entry = new(userId, deviceId);

        cacheService.Add(GetTokenCacheKey(token), entry, CacheTtl);
        cacheService.Add(ownerKey, token, CacheTtl);

        return token;
    }

    public ClipAccessTokenEntry? GetToken(string token)
    {
        if (string.IsNullOrWhiteSpace(token))
            return null;

        string tokenKey = GetTokenCacheKey(token);
        ClipAccessTokenEntry? entry = cacheService.Get<ClipAccessTokenEntry>(tokenKey);
        if (entry is null)
            return null;

        cacheService.Add(tokenKey, entry, CacheTtl);
        cacheService.Add(GetOwnerCacheKey(entry.UserId, entry.DeviceId), token, CacheTtl);
        return entry;
    }
}
