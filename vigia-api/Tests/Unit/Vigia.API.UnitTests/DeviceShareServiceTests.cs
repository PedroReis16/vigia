using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Vigia.API.Contracts;
using Vigia.API.Services.Devices;
using Vigia.Database.Contracts;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.UnitTests;

public class DeviceShareServiceTests : IDisposable
{
    private readonly VigiaDbContext _context;
    private readonly RecordingNotifier _notifier = new();
    private readonly DeviceShareService _service;
    private readonly Guid _ownerId = Guid.NewGuid();
    private readonly Guid _guestId = Guid.NewGuid();
    private readonly Guid _deviceId = Guid.NewGuid();

    public DeviceShareServiceTests()
    {
        _context = CreateContext();
        Guid groupId = Guid.NewGuid();
        User owner = new() { Id = _ownerId, Email = "owner@vigia.test", Phone = "1", LinkedGroups = [] };
        User guest = new() { Id = _guestId, Email = "guest@vigia.test", Phone = "2", LinkedGroups = [] };
        Group group = new()
        {
            Id = groupId,
            OwnerId = _ownerId,
            LinkedUsers = [owner],
            Devices = [],
        };
        _context.Users.Add(guest);
        _context.Groups.Add(group);
        _context.Devices.Add(new Device
        {
            Id = _deviceId,
            Name = "Vigia-0123abcd",
            MacAddress = "aa:bb:cc:dd:ee:ff",
            GroupId = groupId,
        });
        _context.SaveChanges();

        IServiceScopeFactory scopes = new ShareScopeFactory(
            new DevicesDao(_context),
            new GroupDao(_context),
            new GroupInviteDao(_context),
            _notifier);
        DefaultHttpContext http = new();
        http.Request.Scheme = "https";
        http.Request.Host = new HostString("services.example");

        _service = new DeviceShareService(
            NullLogger<DeviceShareService>.Instance,
            scopes,
            new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["BasePath"] = "vigia",
            }).Build(),
            new HttpAccessor(http));
    }

    [Fact]
    public async Task GenerateInviteAsync_ExpiresInFiveMinutes()
    {
        var invite = await _service.GenerateInviteAsync(_deviceId, _ownerId);

        Assert.Equal(TimeSpan.FromMinutes(5), DeviceShareService.InviteLifetime);
        Assert.InRange(
            invite.ExpiresAt,
            DateTime.UtcNow.Add(DeviceShareService.InviteLifetime).AddSeconds(-5),
            DateTime.UtcNow.Add(DeviceShareService.InviteLifetime).AddSeconds(5));
        Assert.StartsWith("https://services.example/vigia/i/", invite.InviteUrl);
    }

    [Fact]
    public async Task AcceptInviteAsync_ExpiredInvite_ReturnsInviteExpired()
    {
        var invite = await _service.GenerateInviteAsync(_deviceId, _ownerId);
        GroupInvite stored = await _context.Set<GroupInvite>().SingleAsync();
        stored.ExpiresAt = DateTime.UtcNow.AddMinutes(-1);
        await _context.SaveChangesAsync();

        EntityValidationException exception = await Assert.ThrowsAsync<EntityValidationException>(
            () => _service.AcceptInviteAsync(invite.Token, _guestId));

        Assert.Equal(ErrorCodes.INVITE_EXPIRED, exception.ErrorCode);
        Assert.Empty(_notifier.Joined);
    }

    [Fact]
    public async Task AcceptInviteAsync_NotifiesOnce()
    {
        var invite = await _service.GenerateInviteAsync(_deviceId, _ownerId);

        await _service.AcceptInviteAsync(invite.Token, _guestId);

        Assert.Single(_notifier.Joined);
    }

    public void Dispose() => _context.Dispose();

    private static VigiaDbContext CreateContext()
    {
        DbContextOptions<VigiaDbContext> options = new DbContextOptionsBuilder<VigiaDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;
        VigiaDbContext context = new(options);
        context.Database.EnsureCreated();
        return context;
    }

    private sealed class RecordingNotifier : IGroupRealtimeNotifier
    {
        public List<Guid> Joined { get; } = [];

        public Task NotifyMembershipJoinedAsync(Guid groupId, Guid userId)
        {
            Joined.Add(userId);
            return Task.CompletedTask;
        }

        public Task NotifyMembershipRemovedAsync(Guid groupId, Guid userId) => Task.CompletedTask;

        public Task NotifyDevicesChangedAsync(Guid groupId, Guid affectedUserId, Guid deviceId) =>
            Task.CompletedTask;
    }

    private sealed class HttpAccessor(HttpContext context) : IHttpContextAccessor
    {
        public HttpContext? HttpContext { get; set; } = context;
    }

    private sealed class ShareScopeFactory(params object[] services) : IServiceScopeFactory
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
