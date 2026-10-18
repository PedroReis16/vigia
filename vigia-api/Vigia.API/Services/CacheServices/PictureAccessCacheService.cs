using System.Security.Cryptography;
using Vigia.API.Contracts.CacheServices;
using Vigia.Cache.Services;

namespace Vigia.API.Services.CacheServices;

/// <summary>
/// Tokens de foto de perfil reutilizáveis dentro do TTL (adequado a img).
/// A validação renova o prazo para a imagem não expirar com a tela aberta.
/// </summary>
internal class PictureAccessCacheService(IRedisCacheService cacheService) : IPictureAccessCacheService
{
    private static readonly TimeSpan CacheTtl = TimeSpan.FromHours(1);

    private static string GetTokenCacheKey(string token) => $"picture-access-{token}";

    private static string GetOwnerCacheKey(Guid viewerId, Guid subjectUserId) =>
        $"picture-access-owner-{viewerId}-{subjectUserId}";

    public string IssueToken(Guid viewerId, Guid subjectUserId)
    {
        string ownerKey = GetOwnerCacheKey(viewerId, subjectUserId);

        string? existingToken = cacheService.Get<string>(ownerKey);
        if (!string.IsNullOrEmpty(existingToken))
        {
            string tokenKey = GetTokenCacheKey(existingToken);
            PictureAccessTokenEntry? existing = cacheService.Get<PictureAccessTokenEntry>(tokenKey);

            if (existing is not null
                && existing.ViewerId == viewerId
                && existing.SubjectUserId == subjectUserId)
            {
                cacheService.Add(tokenKey, existing, CacheTtl);
                cacheService.Add(ownerKey, existingToken, CacheTtl);
                return existingToken;
            }
        }

        string token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant();
        PictureAccessTokenEntry entry = new(viewerId, subjectUserId);

        cacheService.Add(GetTokenCacheKey(token), entry, CacheTtl);
        cacheService.Add(ownerKey, token, CacheTtl);

        return token;
    }

    public PictureAccessTokenEntry? GetToken(string token)
    {
        if (string.IsNullOrWhiteSpace(token))
            return null;

        string tokenKey = GetTokenCacheKey(token);
        PictureAccessTokenEntry? entry = cacheService.Get<PictureAccessTokenEntry>(tokenKey);
        if (entry is null)
            return null;

        cacheService.Add(tokenKey, entry, CacheTtl);
        cacheService.Add(GetOwnerCacheKey(entry.ViewerId, entry.SubjectUserId), token, CacheTtl);
        return entry;
    }
}
