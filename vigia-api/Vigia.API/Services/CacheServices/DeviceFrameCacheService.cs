using Vigia.API.Contracts.CacheServices;
using Vigia.Cache.Services;

namespace Vigia.API.Services.CacheServices;

internal class DeviceFrameCacheService(IRedisCacheService cacheService) : IDeviceFrameCacheService
{
    private static readonly TimeSpan FrameTtl = TimeSpan.FromSeconds(120);

    private static string GetCacheKey(Guid deviceId) => $"device-frame-{deviceId}";

    public bool HasFrame(Guid deviceId)
    {
        byte[]? frame = cacheService.Get<byte[]>(GetCacheKey(deviceId));
        return frame is { Length: > 0 };
    }

    public byte[]? GetFrame(Guid deviceId)
    {
        byte[]? frame = cacheService.Get<byte[]>(GetCacheKey(deviceId));
        if (frame is not { Length: > 0 })
            return null;

        // Copy so callers cannot mutate the buffer that may still be referenced.
        return frame.ToArray();
    }

    public void SetFrame(Guid deviceId, byte[] frame) =>
        cacheService.Add(GetCacheKey(deviceId), frame.ToArray(), FrameTtl);
}
