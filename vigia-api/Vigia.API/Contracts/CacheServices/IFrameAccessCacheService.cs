namespace Vigia.API.Contracts.CacheServices;

public record FrameAccessTokenEntry(Guid UserId, Guid DeviceId);

public interface IFrameAccessCacheService
{
    string IssueToken(Guid userId, Guid deviceId);
    FrameAccessTokenEntry? GetToken(string token);
}
