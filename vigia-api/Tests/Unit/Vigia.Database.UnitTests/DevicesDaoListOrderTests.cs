using Microsoft.EntityFrameworkCore;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Seed;

namespace Vigia.Database.UnitTests;

public class DevicesDaoListOrderTests
{
    [Fact]
    public async Task GetUserDevicesAsync_PutsTestDeviceSeedFirst()
    {
        await using VigiaDbContext context = CreateContext();
        DevicesDao dao = new(context);

        Guid ownerId = Guid.NewGuid();
        Guid groupId = Guid.NewGuid();
        Guid zebraId = Guid.NewGuid();

        User owner = new()
        {
            Id = ownerId,
            FirstName = "Admin",
            LastName = "Vigia",
            Email = "owner-order@vigia.test",
            Phone = "11999990000",
        };

        Group group = new()
        {
            Id = groupId,
            OwnerId = ownerId,
            LinkedUsers = [owner],
        };

        Device zebra = new()
        {
            Id = zebraId,
            Name = "Vigia-zzzz",
            Nickname = "AAA Primeiro Alfabetico",
            MacAddress = "11:22:33:44:55:66",
            Room = DeviceRooms.Kitchen,
            GroupId = groupId,
            CreatedAt = DateTime.UtcNow.AddDays(-1),
        };

        Device cameraTeste = new()
        {
            Id = TestDeviceSeed.Id,
            Name = TestDeviceSeed.Name,
            Nickname = TestDeviceSeed.Nickname,
            MacAddress = TestDeviceSeed.MacAddress,
            Room = TestDeviceSeed.Room,
            GroupId = groupId,
            CreatedAt = TestDeviceSeed.CreatedAt,
        };

        context.Users.Add(owner);
        context.Groups.Add(group);
        context.Devices.AddRange(zebra, cameraTeste);
        await context.SaveChangesAsync();

        List<Device> devices = await dao.GetUserDevicesAsync(ownerId, page: 1, pageSize: 10);

        Assert.Equal(2, devices.Count);
        Assert.Equal(TestDeviceSeed.Id, devices[0].Id);
        Assert.Equal(zebraId, devices[1].Id);
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
