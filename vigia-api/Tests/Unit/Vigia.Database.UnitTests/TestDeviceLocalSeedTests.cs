using Microsoft.EntityFrameworkCore;
using Vigia.Database.Migrations;
using Vigia.Models.Seed;

namespace Vigia.Database.UnitTests;

public class TestDeviceLocalSeedTests
{
    [Fact]
    public void Apply_LinksAdminToTheTestDeviceGroup()
    {
        using VigiaDbContext context = CreateContext();

        TestDeviceLocalSeed.Apply(context, logger: null);
        TestDeviceLocalSeed.Apply(context, logger: null);

        Assert.Equal(TestDeviceSeed.GroupId, context.Devices.Single(d => d.Id == TestDeviceSeed.Id).GroupId);

        var admin = context.Users
            .Include(u => u.LinkedGroups)
            .Single(u => u.Id == TestDeviceSeed.OwnerId);

        Assert.Equal(TestDeviceSeed.OwnerEmail, admin.Email);
        Assert.Contains(admin.LinkedGroups, group => group.Id == TestDeviceSeed.GroupId);
        Assert.Single(context.Devices.Where(d => d.Id == TestDeviceSeed.Id));
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
