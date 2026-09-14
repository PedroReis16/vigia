namespace Vigia.API.Contracts.CacheServices;

public interface IDeviceIdentityCacheService
{
    string? GetSignPublicKey(Guid deviceId);
    void SetSignPublicKey(Guid deviceId, string signPublicKey);
}
