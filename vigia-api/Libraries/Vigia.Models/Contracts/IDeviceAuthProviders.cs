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

public interface IPictureAccessTokenProvider
{
    string IssueToken(Guid viewerId, Guid subjectUserId);
    bool TryValidate(string token, Guid subjectUserId, out Guid viewerId);
}
