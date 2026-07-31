namespace Vigia.API.Contracts.CacheServices;

public interface IDeviceFrameCacheService
{
    byte[]? GetFrame(Guid deviceId);
    void SetFrame(Guid deviceId, byte[] frame);
}