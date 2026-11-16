namespace Vigia.API.Contracts.CacheServices;

public record ClipAccessTokenEntry(Guid UserId, Guid DeviceId);

public interface IClipAccessCacheService
{
    string IssueToken(Guid userId, Guid deviceId);
    ClipAccessTokenEntry? GetToken(string token);
}
