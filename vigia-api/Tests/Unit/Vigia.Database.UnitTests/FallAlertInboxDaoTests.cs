using Microsoft.EntityFrameworkCore;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.Database.UnitTests;

public class FallAlertInboxDaoTests
{
    [Fact]
    public async Task FindActiveByDevice_IgnoresAcknowledgedEpisodes()
    {
        await using VigiaDbContext context = CreateContext();
        FallAlertEpisodeDao dao = new(context);

        Guid deviceId = Guid.NewGuid();
        Guid groupId = Guid.NewGuid();

        await dao.AddAsync(new FallAlertEpisode
        {
            DeviceId = deviceId,
            GroupId = groupId,
            Status = FallAlertEpisodeStatus.Acknowledged,
            FirstDetectedAt = DateTime.UtcNow.AddMinutes(-10),
            LastNotifiedAt = DateTime.UtcNow.AddMinutes(-10),
            NotifyCount = 1,
        });

        FallAlertEpisode? active = await dao.FindActiveByDeviceAsync(deviceId);
        Assert.Null(active);

        await dao.AddAsync(new FallAlertEpisode
        {
            DeviceId = deviceId,
            GroupId = groupId,
            Status = FallAlertEpisodeStatus.Active,
            FirstDetectedAt = DateTime.UtcNow,
            LastNotifiedAt = DateTime.UtcNow,
            NotifyCount = 1,
            NextRetryAt = DateTime.UtcNow.AddMinutes(2),
        });

        FallAlertEpisode? found = await dao.FindActiveByDeviceAsync(deviceId);
        Assert.NotNull(found);
        Assert.Equal(FallAlertEpisodeStatus.Active, found!.Status);
    }

    [Fact]
    public async Task MarkReadByEpisodes_OnlyMarksUnreadForUser()
    {
        await using VigiaDbContext context = CreateContext();
        UserNotificationDao dao = new(context);

        Guid userA = Guid.NewGuid();
        Guid userB = Guid.NewGuid();
        Guid episodeId = Guid.NewGuid();
        Guid deviceId = Guid.NewGuid();

        await dao.AddRangeAsync(
        [
            new UserNotification
            {
                UserId = userA,
                EpisodeId = episodeId,
                DeviceId = deviceId,
                Type = "fall",
                Title = "Alerta de queda",
                Body = "Queda detectada",
            },
            new UserNotification
            {
                UserId = userB,
                EpisodeId = episodeId,
                DeviceId = deviceId,
                Type = "fall",
                Title = "Alerta de queda",
                Body = "Queda detectada",
            },
        ]);

        DateTime now = DateTime.UtcNow;
        await dao.MarkReadByEpisodesAsync(userA, [episodeId], now);

        (List<UserNotification> itemsA, int unreadA) = await dao.ListByUserAsync(userA, 0, 20);
        (List<UserNotification> itemsB, int unreadB) = await dao.ListByUserAsync(userB, 0, 20);

        Assert.Equal(0, unreadA);
        Assert.NotNull(itemsA[0].ReadAt);
        Assert.Equal(1, unreadB);
        Assert.Null(itemsB[0].ReadAt);
    }

    [Fact]
    public async Task ListDueForRetry_ReturnsOnlyActiveWithNextRetryInPast()
    {
        await using VigiaDbContext context = CreateContext();
        FallAlertEpisodeDao dao = new(context);

        Guid deviceId = Guid.NewGuid();
        Guid otherDeviceId = Guid.NewGuid();
        Guid groupId = Guid.NewGuid();
        DateTime now = DateTime.UtcNow;

        context.Groups.Add(new Group { Id = groupId, OwnerId = Guid.NewGuid(), LinkedUsers = [], Devices = [] });
        context.Devices.AddRange(
            new Device { Id = deviceId, Name = "Vigia-a1b2c3d4", MacAddress = "AA:BB:CC:DD:EE:01", GroupId = groupId },
            new Device { Id = otherDeviceId, Name = "Vigia-b2c3d4e5", MacAddress = "AA:BB:CC:DD:EE:02", GroupId = groupId });
        await context.SaveChangesAsync();

        await dao.AddAsync(new FallAlertEpisode
        {
            DeviceId = deviceId,
            GroupId = groupId,
            Status = FallAlertEpisodeStatus.Active,
            FirstDetectedAt = now.AddMinutes(-5),
            LastNotifiedAt = now.AddMinutes(-5),
            NotifyCount = 1,
            NextRetryAt = now.AddMinutes(-1),
        });

        await dao.AddAsync(new FallAlertEpisode
        {
            DeviceId = otherDeviceId,
            GroupId = groupId,
            Status = FallAlertEpisodeStatus.Active,
            FirstDetectedAt = now,
            LastNotifiedAt = now,
            NotifyCount = 1,
            NextRetryAt = now.AddMinutes(5),
        });

        List<FallAlertEpisode> due = await dao.ListDueForRetryAsync(now);
        Assert.Single(due);
        Assert.Equal(deviceId, due[0].DeviceId);
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
