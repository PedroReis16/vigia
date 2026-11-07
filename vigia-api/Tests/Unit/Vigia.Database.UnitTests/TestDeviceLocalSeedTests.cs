using Microsoft.EntityFrameworkCore;
using Vigia.Database.Migrations;
using Vigia.Models.Seed;

namespace Vigia.Database.UnitTests;

public class TestDeviceLocalSeedTests
{
    [Fact]
    public void Apply_SeedsFullMockPoolAndLinksAdmin()
    {
        using VigiaDbContext context = CreateContext();

        TestDeviceLocalSeed.Apply(context, logger: null);
        TestDeviceLocalSeed.Apply(context, logger: null);

        Assert.Equal(MockDevicesSeed.All.Count, context.Devices.Count());
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
    public void TestDeviceSeed_MatchesPrimaryMockSlot()
    {
        Assert.Equal(TestDeviceSeed.Id, MockDevicesSeed.Primary.Id);
        Assert.Equal(TestDeviceSeed.Name, MockDevicesSeed.Primary.Name);
        Assert.Equal(TestDeviceSeed.MacAddress, MockDevicesSeed.Primary.MacAddress);
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
