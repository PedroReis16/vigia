using Vigia.API.Contracts.CacheServices;
using Vigia.Models.Contracts;

namespace Vigia.API.Services;

internal class PictureAccessTokenProvider(IPictureAccessCacheService pictureAccessCache) : IPictureAccessTokenProvider
{
    public string IssueToken(Guid viewerId, Guid subjectUserId) =>
        pictureAccessCache.IssueToken(viewerId, subjectUserId);

    public bool TryValidate(string token, Guid subjectUserId, out Guid viewerId)
    {
        viewerId = Guid.Empty;

        PictureAccessTokenEntry? entry = pictureAccessCache.GetToken(token);
        if (entry == null || entry.SubjectUserId != subjectUserId)
            return false;

        viewerId = entry.ViewerId;
        return true;
    }
}
