using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Vigia.API.Hubs;
using Vigia.API.Models.DTOs.Realtime;
using Vigia.API.Services;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;

namespace Vigia.API.UnitTests;

public class GroupRealtimeNotifierTests
{
    [Fact]
    public async Task NotifyMembershipJoinedAsync_SendsOncePerRecipient()
    {
        await using VigiaDbContext context = CreateContext();
        Guid groupId = Guid.NewGuid();
        Guid ownerId = Guid.NewGuid();
        Guid memberId = Guid.NewGuid();
        User owner = new() { Id = ownerId, Email = "owner@vigia.test", Phone = "1", LinkedGroups = [] };
        User member = new() { Id = memberId, Email = "member@vigia.test", Phone = "2", LinkedGroups = [] };
        context.Groups.Add(new Group
        {
            Id = groupId,
            OwnerId = ownerId,
            LinkedUsers = [owner, member],
            Devices = [],
        });
        context.Devices.Add(new Device
        {
            Id = Guid.NewGuid(),
            Name = "Vigia-0123abcd",
            MacAddress = "aa:bb:cc:dd:ee:01",
            GroupId = groupId,
        });
        await context.SaveChangesAsync();

        RecordingClients clients = new();
        GroupRealtimeNotifier notifier = new(
            new RecordingHubContext(clients),
            new NotifierScopeFactory(new UserDao(context), new DevicesDao(context)),
            NullLogger<GroupRealtimeNotifier>.Instance);

        await notifier.NotifyMembershipJoinedAsync(groupId, memberId);

        Assert.Equal(2, clients.GroupCalls);
        Assert.Contains($"user:{ownerId:D}", clients.GroupNames);
        Assert.Contains($"user:{memberId:D}", clients.GroupNames);
        Assert.Equal(2, clients.Proxy.Payloads.Count);
        Assert.All(clients.Proxy.Payloads, payload => Assert.Equal("joined", payload.ChangeType));
    }

    [Fact]
    public async Task NotifyDevicesChangedAsync_IncludesTheAffectedDevice()
    {
        await using VigiaDbContext context = CreateContext();
        Guid groupId = Guid.NewGuid();
        Guid ownerId = Guid.NewGuid();
        Guid deviceId = Guid.NewGuid();
        User owner = new() { Id = ownerId, Email = "owner@vigia.test", Phone = "1", LinkedGroups = [] };
        context.Groups.Add(new Group
        {
            Id = groupId,
            OwnerId = ownerId,
            LinkedUsers = [owner],
            Devices = [],
        });
        await context.SaveChangesAsync();

        RecordingClients clients = new();
        GroupRealtimeNotifier notifier = new(
            new RecordingHubContext(clients),
            new NotifierScopeFactory(new UserDao(context), new DevicesDao(context)),
            NullLogger<GroupRealtimeNotifier>.Instance);

        await notifier.NotifyDevicesChangedAsync(groupId, ownerId, deviceId);

        GroupMembershipChangedDTO payload = Assert.Single(clients.Proxy.Payloads);
        Assert.Equal(GroupRealtimeNotifier.DevicesChangedType, payload.ChangeType);
        Assert.Contains(deviceId, payload.DeviceIds);
    }

    [Fact]
    public void UserGroupName_CanonicalizesGuidCase()
    {
        const string raw = "91137D79-ED96-40E0-8C11-87B055C61BC8";
        Assert.Equal(
            "user:91137d79-ed96-40e0-8c11-87b055c61bc8",
            DeviceGroupsHub.UserGroupName(raw));
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

    private sealed class RecordingProxy : IClientProxy
    {
        public List<GroupMembershipChangedDTO> Payloads { get; } = [];

        public Task SendCoreAsync(string method, object?[] args, CancellationToken cancellationToken = default)
        {
            Payloads.Add(Assert.IsType<GroupMembershipChangedDTO>(args[0]));
            return Task.CompletedTask;
        }
    }

    private sealed class RecordingClients : IHubClients
    {
        public RecordingProxy Proxy { get; } = new();
        public int GroupCalls { get; private set; }
        public List<string> GroupNames { get; } = [];

        public IClientProxy All => throw new NotSupportedException();
        public IClientProxy AllExcept(IReadOnlyList<string> excludedConnectionIds) => throw new NotSupportedException();
        public IClientProxy Client(string connectionId) => throw new NotSupportedException();
        public IClientProxy Clients(IReadOnlyList<string> connectionIds) => throw new NotSupportedException();
        public IClientProxy Group(string groupName)
        {
            GroupCalls++;
            GroupNames.Add(groupName);
            return Proxy;
        }
        public IClientProxy GroupExcept(string groupName, IReadOnlyList<string> excludedConnectionIds) => throw new NotSupportedException();
        public IClientProxy Groups(IReadOnlyList<string> groupNames) => throw new NotSupportedException();
        public IClientProxy User(string userId) => throw new NotSupportedException();
        public IClientProxy Users(IReadOnlyList<string> userIds) => throw new NotSupportedException();
    }

    private sealed class RecordingHubContext(RecordingClients clients) : IHubContext<DeviceGroupsHub>
    {
        public IHubClients Clients { get; } = clients;
        public IGroupManager Groups => throw new NotSupportedException();
    }

    private sealed class NotifierScopeFactory(params object[] services) : IServiceScopeFactory
    {
        public IServiceScope CreateScope() => new Scope(services);

        private sealed class Scope(object[] services) : IServiceScope
        {
            public IServiceProvider ServiceProvider { get; } = new Provider(services);
            public void Dispose() { }
        }

        private sealed class Provider(object[] services) : IServiceProvider
        {
            public object? GetService(Type serviceType) =>
                services.FirstOrDefault(service => serviceType.IsInstanceOfType(service));
        }
    }
}
