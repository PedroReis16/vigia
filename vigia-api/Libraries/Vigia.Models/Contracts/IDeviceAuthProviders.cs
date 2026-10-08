namespace Vigia.Models.Contracts;

public interface IFrameAccessTokenProvider
{
    string IssueToken(Guid userId, Guid deviceId);
    bool TryValidate(string token, Guid deviceId, out Guid userId);
}

public interface IClipAccessTokenProvider
{
    string IssueToken(Guid userId, Guid deviceId);
    bool TryValidate(string token, Guid deviceId, out Guid userId);
}
