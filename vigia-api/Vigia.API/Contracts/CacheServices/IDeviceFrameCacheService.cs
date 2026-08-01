namespace Vigia.API.Contracts.CacheServices;

public interface IDeviceFrameCacheService
{
    bool HasFrame(Guid deviceId);
    byte[]? GetFrame(Guid deviceId);
    void SetFrame(Guid deviceId, byte[] frame);
}
