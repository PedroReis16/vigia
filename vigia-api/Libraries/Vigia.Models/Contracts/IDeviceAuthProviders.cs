namespace Vigia.Models.Contracts;

public interface IDeviceSignPublicKeyProvider
{
    Task<string?> GetSignPublicKeyAsync(Guid deviceId);
    void SetSignPublicKey(Guid deviceId, string signPublicKey);
}

public interface IFrameAccessTokenProvider
{
    string IssueToken(Guid userId, Guid deviceId);
    bool TryValidate(string token, Guid deviceId, out Guid userId);
}
