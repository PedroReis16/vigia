using Microsoft.EntityFrameworkCore;
using Vigia.Database.Migrations;
using Vigia.Models.Seed;

namespace Vigia.Database.UnitTests;

public class TestDeviceLocalSeedTests
{
    [Fact]
    public void Apply_SeedsEdgeTestDeviceAndMockPool()
    {
        using VigiaDbContext context = CreateContext();

        TestDeviceLocalSeed.Apply(context, logger: null);
        TestDeviceLocalSeed.Apply(context, logger: null);

        int expectedCount = 1 + MockDevicesSeed.All.Count;
        Assert.Equal(expectedCount, context.Devices.Count());

        Assert.Equal(TestDeviceSeed.GroupId, context.Devices.Single(d => d.Id == TestDeviceSeed.Id).GroupId);
        Assert.DoesNotContain(MockDevicesSeed.All, d => d.Id == TestDeviceSeed.Id);

        Assert.All(
            MockDevicesSeed.All,
            definition =>
            {
                var device = context.Devices.Single(d => d.Id == definition.Id);
                Assert.Equal(MockDevicesSeed.GroupId, device.GroupId);
                Assert.Equal(definition.Name, device.Name);
                Assert.Equal(definition.Nickname, device.Nickname);
            });

        var admin = context.Users
            .Include(u => u.LinkedGroups)
            .Single(u => u.Id == TestDeviceSeed.OwnerId);

        Assert.Equal(TestDeviceSeed.OwnerEmail, admin.Email);
        Assert.Contains(admin.LinkedGroups, group => group.Id == TestDeviceSeed.GroupId);
    }

    [Fact]
    public void MockPool_NeverIncludesEdgeTestDevice()
    {
        Assert.DoesNotContain(MockDevicesSeed.All, d => d.Id == TestDeviceSeed.Id);
        Assert.DoesNotContain(MockDevicesSeed.All, d => d.Name == TestDeviceSeed.Name);
        Assert.DoesNotContain(MockDevicesSeed.All, d => d.MacAddress == TestDeviceSeed.MacAddress);
    }

    private static VigiaDbContext CreateContext()
    {
        DbContextOptions<VigiaDbContext> options = new DbContextOptionsBuilder<VigiaDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;

        VigiaDbContext context = new(options);
        context.Database.EnsureCreated();
        return context;
    }
}
