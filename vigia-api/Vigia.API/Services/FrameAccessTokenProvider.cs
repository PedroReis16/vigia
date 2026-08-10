using Vigia.API.Contracts.CacheServices;
using Vigia.Models.Contracts;

namespace Vigia.API.Services;

internal class FrameAccessTokenProvider(IFrameAccessCacheService frameAccessCache) : IFrameAccessTokenProvider
{
    public string IssueToken(Guid userId, Guid deviceId) => frameAccessCache.IssueToken(userId, deviceId);

    public bool TryValidate(string token, Guid deviceId, out Guid userId)
    {
        userId = Guid.Empty;

        FrameAccessTokenEntry? entry = frameAccessCache.GetToken(token);
        if (entry == null || entry.DeviceId != deviceId)
            return false;

        userId = entry.UserId;
        return true;
    }
}
