using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using Vigia.API.Config;
using Vigia.API.Services;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.API.UnitTests;

public class NotificationInboxServiceTests
{
    [Fact]
    public async Task AcknowledgeDeviceAlerts_StopsRetriesAndMarksActorNotificationsRead()
    {
        await using VigiaDbContext context = CreateContext();

        Guid ownerId = Guid.NewGuid();
        Guid memberId = Guid.NewGuid();
        Guid groupId = Guid.NewGuid();
        Guid deviceId = Guid.NewGuid();

        context.Users.AddRange(
            new User { Id = ownerId, Email = "owner@vigia.test", Phone = "1" },
            new User { Id = memberId, Email = "member@vigia.test", Phone = "2" });
        context.Groups.Add(new Group
        {
            Id = groupId,
            OwnerId = ownerId,
            LinkedUsers = [],
            Devices = [],
        });
        context.Devices.Add(new Device
        {
            Id = deviceId,
            Name = "Vigia-a1b2c3d4",
            MacAddress = "AA:BB:CC:DD:EE:FF",
            GroupId = groupId,
        });
        await context.SaveChangesAsync();

        GroupDao groupDao = new(context);
        await groupDao.AddUserToGroupAsync(groupId, ownerId);
        await groupDao.AddUserToGroupAsync(groupId, memberId);

        FallAlertEpisodeDao episodeDao = new(context);
        UserNotificationDao notificationDao = new(context);

        FallAlertEpisode episode = new()
        {
            DeviceId = deviceId,
            GroupId = groupId,
            Status = FallAlertEpisodeStatus.Active,
            FirstDetectedAt = DateTime.UtcNow.AddMinutes(-3),
            LastNotifiedAt = DateTime.UtcNow.AddMinutes(-3),
            NotifyCount = 2,
            NextRetryAt = DateTime.UtcNow.AddMinutes(1),
        };
        await episodeDao.AddAsync(episode);

        await notificationDao.AddRangeAsync(
        [
            new UserNotification
            {
                UserId = ownerId,
                EpisodeId = episode.Id,
                DeviceId = deviceId,
                Type = "fall",
                Title = "Alerta de queda",
                Body = "Queda detectada em Sala",
            },
            new UserNotification
            {
                UserId = memberId,
                EpisodeId = episode.Id,
                DeviceId = deviceId,
                Type = "fall",
                Title = "Alerta de queda",
                Body = "Queda detectada em Sala",
            },
        ]);

        NotificationInboxService service = new(
            notificationDao,
            episodeDao,
            new DevicesDao(context),
            groupDao,
            Options.Create(new AlertOptions()));

        await service.AcknowledgeDeviceAlertsAsync(ownerId, deviceId);

        FallAlertEpisode? updated = await episodeDao.FindAsync(episode.Id);
        Assert.NotNull(updated);
        Assert.Equal(FallAlertEpisodeStatus.Acknowledged, updated!.Status);
        Assert.Null(updated.NextRetryAt);
        Assert.Equal(ownerId, updated.AcknowledgedByUserId);

        (_, int unreadOwner) = await notificationDao.ListByUserAsync(ownerId, 0, 20);
        (_, int unreadMember) = await notificationDao.ListByUserAsync(memberId, 0, 20);
        Assert.Equal(0, unreadOwner);
        Assert.Equal(1, unreadMember);
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
