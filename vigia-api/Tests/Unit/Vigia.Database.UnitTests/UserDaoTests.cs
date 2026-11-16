using Microsoft.EntityFrameworkCore;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;

namespace Vigia.Database.UnitTests;

public class UserDaoTests
{
    [Fact]
    public async Task GetUsersByGroupAsync_ReturnsOnlyActiveMembersOfTheGroup()
    {
        await using VigiaDbContext context = CreateContext();
        UserDao dao = new(context);

        Guid groupId = Guid.NewGuid();
        Guid ownerId = Guid.NewGuid();
        Guid memberId = Guid.NewGuid();
        Guid removedId = Guid.NewGuid();
        Guid otherGroupId = Guid.NewGuid();
        Guid outsiderId = Guid.NewGuid();

        User owner = User(ownerId, "owner@vigia.test");
        User member = User(memberId, "member@vigia.test");
        User removed = User(removedId, "removed@vigia.test");
        removed.DeletedAt = DateTime.UtcNow;
        User outsider = User(outsiderId, "outsider@vigia.test");

        Group group = new()
        {
            Id = groupId,
            OwnerId = ownerId,
            LinkedUsers = [owner, member, removed],
        };
        Group otherGroup = new()
        {
            Id = otherGroupId,
            OwnerId = outsiderId,
            LinkedUsers = [outsider],
        };

        context.Users.AddRange(owner, member, removed, outsider);
        context.Groups.AddRange(group, otherGroup);
        await context.SaveChangesAsync();

        List<User> users = await dao.GetUsersByGroupAsync(groupId);

        Assert.Equal(2, users.Count);
        Assert.Contains(users, user => user.Id == ownerId && user.Email == "owner@vigia.test");
        Assert.Contains(users, user => user.Id == memberId);
        Assert.DoesNotContain(users, user => user.Id == removedId);
        Assert.DoesNotContain(users, user => user.Id == outsiderId);
    }

    [Fact]
    public async Task FindWithGroupsAsync_LoadsTheOwnedGroupAndSkipsDeletedUsers()
    {
        await using VigiaDbContext context = CreateContext();
        UserDao dao = new(context);

        Guid userId = Guid.NewGuid();
        Guid groupId = Guid.NewGuid();
        User user = User(userId, "ana@vigia.test");
        Group group = new()
        {
            Id = groupId,
            OwnerId = userId,
            LinkedUsers = [user],
        };

        context.Users.Add(user);
        context.Groups.Add(group);
        await context.SaveChangesAsync();

        User? found = await dao.FindWithGroupsAsync(userId);

        Assert.NotNull(found);
        Assert.Contains(found.LinkedGroups, linked => linked.Id == groupId && linked.OwnerId == userId);

        user.DeletedAt = DateTime.UtcNow;
        context.Users.Update(user);
        await context.SaveChangesAsync();

        Assert.Null(await dao.FindWithGroupsAsync(userId));
    }

    private static User User(Guid id, string email) => new()
    {
        Id = id,
        Email = email,
        Phone = "11999990000",
        LinkedGroups = [],
    };

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
