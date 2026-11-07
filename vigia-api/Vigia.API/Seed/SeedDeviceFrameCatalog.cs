using System.Reflection;
using Vigia.Models.Seed;

namespace Vigia.API.Seed;

/// <summary>
/// JPEGs embutidos para thumbnails DEBUG (edge de teste + pool mock).
/// </summary>
internal static class SeedDeviceFrameCatalog
{
    private static readonly Lazy<IReadOnlyDictionary<Guid, byte[]>> Frames = new(Load);

    public static IReadOnlyDictionary<Guid, byte[]> All => Frames.Value;

    public static bool TryGet(Guid deviceId, out byte[] jpeg) =>
        Frames.Value.TryGetValue(deviceId, out jpeg!);

    public static IEnumerable<Guid> DeviceIds
    {
        get
        {
            yield return TestDeviceSeed.Id;
            foreach (MockDeviceDefinition device in MockDevicesSeed.All)
                yield return device.Id;
        }
    }

    private static IReadOnlyDictionary<Guid, byte[]> Load()
    {
        Assembly assembly = typeof(SeedDeviceFrameCatalog).Assembly;
        string prefix = typeof(SeedDeviceFrameCatalog).Namespace + ".Frames.";
        Dictionary<Guid, byte[]> map = [];

        foreach (string resourceName in assembly.GetManifestResourceNames())
        {
            if (!resourceName.StartsWith(prefix, StringComparison.Ordinal)
                || !resourceName.EndsWith(".jpg", StringComparison.OrdinalIgnoreCase))
                continue;

            string fileName = resourceName[prefix.Length..];
            string idText = Path.GetFileNameWithoutExtension(fileName);
            if (!Guid.TryParse(idText, out Guid deviceId))
                continue;

            using Stream? stream = assembly.GetManifestResourceStream(resourceName);
            if (stream is null)
                continue;

            using MemoryStream buffer = new();
            stream.CopyTo(buffer);
            byte[] jpeg = buffer.ToArray();
            if (jpeg.Length > 0)
                map[deviceId] = jpeg;
        }

        return map;
    }
}
