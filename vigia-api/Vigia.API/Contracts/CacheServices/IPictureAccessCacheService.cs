namespace Vigia.API.Contracts.CacheServices;

public record PictureAccessTokenEntry(Guid ViewerId, Guid SubjectUserId);

public interface IPictureAccessCacheService
{
    string IssueToken(Guid viewerId, Guid subjectUserId);
    PictureAccessTokenEntry? GetToken(string token);
}
