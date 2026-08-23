using Microsoft.EntityFrameworkCore;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;

namespace Vigia.Database.UnitTests;

public class UserPushTokenDaoTests
{
    [Fact]
    public async Task UpsertAsync_AfterSoftDelete_ReactivatesSameToken()
    {
        await using VigiaDbContext context = CreateContext();
        UserPushTokenDao dao = new(context);

        Guid userId = Guid.NewGuid();
        const string token = "fcm-token-device-1";
        const string platform = "android";

        await dao.UpsertAsync(userId, token, platform);
        await dao.DeleteByTokenAsync(token);

        UserPushToken softDeleted = await context.UserPushTokens.SingleAsync(t => t.Token == token);
        Assert.NotNull(softDeleted.DeletedAt);

        await dao.UpsertAsync(userId, token, platform);

        List<UserPushToken> rows = await context.UserPushTokens.Where(t => t.Token == token).ToListAsync();
        Assert.Single(rows);
        Assert.Null(rows[0].DeletedAt);
        Assert.Equal(userId, rows[0].UserId);
        Assert.Equal(platform, rows[0].Platform);

        List<string> activeTokens = await dao.GetTokensByUserIdsAsync([userId]);
        Assert.Contains(token, activeTokens);
    }

    [Fact]
    public async Task UpsertAsync_ExistingActiveToken_UpdatesWithoutDuplicating()
    {
        await using VigiaDbContext context = CreateContext();
        UserPushTokenDao dao = new(context);

        Guid firstUser = Guid.NewGuid();
        Guid secondUser = Guid.NewGuid();
        const string token = "fcm-token-shared-device";

        await dao.UpsertAsync(firstUser, token, "android");
        await dao.UpsertAsync(secondUser, token, "ios");

        List<UserPushToken> rows = await context.UserPushTokens.Where(t => t.Token == token).ToListAsync();
        Assert.Single(rows);
        Assert.Equal(secondUser, rows[0].UserId);
        Assert.Equal("ios", rows[0].Platform);
        Assert.Null(rows[0].DeletedAt);
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
