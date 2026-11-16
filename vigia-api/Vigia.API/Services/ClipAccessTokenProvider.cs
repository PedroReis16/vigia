using Vigia.API.Contracts.CacheServices;
using Vigia.Models.Contracts;

namespace Vigia.API.Services;

internal class ClipAccessTokenProvider(IClipAccessCacheService clipAccessCache) : IClipAccessTokenProvider
{
    public string IssueToken(Guid userId, Guid deviceId) => clipAccessCache.IssueToken(userId, deviceId);

    public bool TryValidate(string token, Guid deviceId, out Guid userId)
    {
        userId = Guid.Empty;

        ClipAccessTokenEntry? entry = clipAccessCache.GetToken(token);
        if (entry == null || entry.DeviceId != deviceId)
            return false;

        userId = entry.UserId;
        return true;
    }
}
