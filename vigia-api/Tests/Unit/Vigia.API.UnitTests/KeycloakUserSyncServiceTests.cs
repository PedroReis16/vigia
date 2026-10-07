using Microsoft.EntityFrameworkCore;
using Vigia.API.Models.DTOs.Users;
using Vigia.API.Services;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;

namespace Vigia.API.UnitTests;

public class KeycloakUserSyncServiceTests
{
    [Fact]
    public async Task ApplyAsync_Upsert_CreatesThenUpdatesTheSameUser()
    {
        await using VigiaDbContext context = CreateContext();
        KeycloakUserSyncService service = CreateService(context);
        Guid userId = Guid.NewGuid();

        await service.ApplyAsync(new KeycloakUserSyncMessage
        {
            Operation = "upsert",
            Id = userId,
            Email = "ana@vigia.test",
            Phone = "11999990000",
        });

        await service.ApplyAsync(new KeycloakUserSyncMessage
        {
            Operation = "upsert",
            Id = userId,
            Email = "ana.maria@vigia.test",
            Phone = "11988880000",
        });

        List<User> users = await context.Users.Where(u => u.Id == userId).ToListAsync();
        Assert.Single(users);
        Assert.Equal(userId, users[0].Id);
        Assert.Equal("ana.maria@vigia.test", users[0].Email);
        Assert.Equal("11988880000", users[0].Phone);
        Assert.Null(users[0].DeletedAt);
    }

    [Fact]
    public async Task ApplyAsync_Upsert_ReactivatesSoftDeletedUser()
    {
        await using VigiaDbContext context = CreateContext();
        KeycloakUserSyncService service = CreateService(context);
        Guid userId = Guid.NewGuid();

        await service.ApplyAsync(new KeycloakUserSyncMessage
        {
            Operation = "upsert",
            Id = userId,
            Email = "ana@vigia.test",
            Phone = "11999990000",
        });
        await service.ApplyAsync(new KeycloakUserSyncMessage { Operation = "delete", Id = userId });

        await service.ApplyAsync(new KeycloakUserSyncMessage
        {
            Operation = "upsert",
            Id = userId,
            Email = "ana@vigia.test",
            Phone = "11999990000",
        });

        User user = await context.Users.SingleAsync(u => u.Id == userId);
        Assert.Null(user.DeletedAt);
    }

    [Fact]
    public async Task ApplyAsync_Delete_SoftDeletesUserAndPushTokens()
    {
        await using VigiaDbContext context = CreateContext();
        UserPushTokenDao pushTokenDao = new(context);
        KeycloakUserSyncService service = new(new UserDao(context), pushTokenDao, new GroupDao(context));
        Guid userId = Guid.NewGuid();

        await service.ApplyAsync(new KeycloakUserSyncMessage
        {
            Operation = "upsert",
            Id = userId,
            FirstName = "Ana",
            LastName = "Lima",
            Email = "ana@vigia.test",
            Phone = "11999990000",
        });
        await pushTokenDao.UpsertAsync(userId, "fcm-token-1", "android");

        await service.ApplyAsync(new KeycloakUserSyncMessage { Operation = "delete", Id = userId });

        User user = await context.Users.SingleAsync(u => u.Id == userId);
        UserPushToken token = await context.UserPushTokens.SingleAsync(t => t.Token == "fcm-token-1");
        Assert.NotNull(user.DeletedAt);
        Assert.NotNull(token.DeletedAt);
        Assert.Empty(await pushTokenDao.GetTokensByUserIdsAsync([userId]));
    }

    [Fact]
    public async Task ApplyAsync_Upsert_LinksOwnerToTheirGroup()
    {
        await using VigiaDbContext context = CreateContext();
        KeycloakUserSyncService service = CreateService(context);
        Guid adminId = new("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b");

        await service.ApplyAsync(new KeycloakUserSyncMessage
        {
            Operation = "upsert",
            Id = adminId,
            Email = "admin@vigia.local",
            Phone = "11999999999",
        });

        User user = await context.Users.Include(u => u.LinkedGroups).SingleAsync(u => u.Id == adminId);
        Assert.Contains(user.LinkedGroups, group => group.Id == new Guid("80eed123-8e77-47a3-8fae-cedb1ab3eef7"));
    }

    private static KeycloakUserSyncService CreateService(VigiaDbContext context)
    {
        return new KeycloakUserSyncService(new UserDao(context), new UserPushTokenDao(context), new GroupDao(context));
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
