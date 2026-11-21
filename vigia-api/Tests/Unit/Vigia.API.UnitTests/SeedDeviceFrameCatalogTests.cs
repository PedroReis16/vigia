using Vigia.API.Seed;
using Vigia.Models.Seed;

namespace Vigia.API.UnitTests;

public class SeedDeviceFrameCatalogTests
{
    [Fact]
    public void All_ContainsJpegForMockPoolOnly()
    {
        Assert.False(SeedDeviceFrameCatalog.TryGet(TestDeviceSeed.Id, out _));

        foreach (MockDeviceDefinition device in MockDevicesSeed.All)
        {
            Assert.True(
                SeedDeviceFrameCatalog.TryGet(device.Id, out byte[] jpeg),
                $"JPEG ausente para {device.Name} ({device.Id})");
            Assert.True(IsJpeg(jpeg));
        }

        Assert.Equal(MockDevicesSeed.All.Count, SeedDeviceFrameCatalog.All.Count);
        Assert.Equal(MockDevicesSeed.All.Count, SeedDeviceFrameCatalog.DeviceIds.Count());
    }

    private static bool IsJpeg(byte[] bytes) =>
        bytes.Length > 3
        && bytes[0] == 0xFF
        && bytes[1] == 0xD8
        && bytes[^2] == 0xFF
        && bytes[^1] == 0xD9;
}
