using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Vigia.API.Contracts;
using Vigia.API.Services;
using Vigia.API.Services.Devices;
using Vigia.Database.EFDao;
using Vigia.Models.Entities;

namespace Vigia.API.UnitTests;

public class DevicesServiceShareRealtimeTests : IDisposable
{
    private readonly VigiaDbContext _context = CreateContext();
    private readonly RecordingNotifier _notifier = new();
    private readonly Guid _ownerId = Guid.NewGuid();
    private readonly Guid _groupId = Guid.NewGuid();
    private readonly Guid _deviceId = Guid.NewGuid();
    private readonly DevicesService _service;

    public DevicesServiceShareRealtimeTests()
    {
        User owner = new() { Id = _ownerId, Email = "owner@vigia.test", Phone = "1", LinkedGroups = [] };
        Group group = new()
        {
            Id = _groupId,
            OwnerId = _ownerId,
            LinkedUsers = [owner],
            Devices = [],
        };
        _context.Groups.Add(group);
        _context.Devices.Add(new Device
        {
            Id = _deviceId,
            Name = "Vigia-0123abcd",
            MacAddress = "aa:bb:cc:dd:ee:02",
        });
        _context.SaveChanges();

        _service = new DevicesService(
            NullLogger<DevicesService>.Instance,
            new ShareScopeFactory(new DevicesDao(_context), new UserDao(_context), _notifier),
            new ConfigurationBuilder().Build(),
            new DeviceCertificateAuthority(new ConfigurationBuilder().Build(), new ShareScopeFactory(new DevicesDao(_context), new UserDao(_context), _notifier)));
    }

    [Fact]
    public async Task TrackDeviceUserAsync_NotifiesDevicesChanged()
    {
        await _service.TrackDeviceUserAsync(_deviceId, _ownerId);

        Assert.Equal([_deviceId], _notifier.Devices);
        Device stored = await _context.Devices.SingleAsync(device => device.Id == _deviceId);
        Assert.Equal(_groupId, stored.GroupId);
    }

    [Fact]
    public async Task UntrackedDeviceUserAsync_NotifiesDevicesChanged()
    {
        Device device = await _context.Devices.SingleAsync(item => item.Id == _deviceId);
        device.GroupId = _groupId;
        await _context.SaveChangesAsync();

        await _service.UntrackedDeviceUserAsync(_deviceId, _ownerId);

        Assert.Equal([_deviceId], _notifier.Devices);
        Device stored = await _context.Devices.SingleAsync(item => item.Id == _deviceId);
        Assert.Null(stored.GroupId);
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
        public List<Guid> Devices { get; } = [];

        public Task NotifyMembershipJoinedAsync(Guid groupId, Guid userId) => Task.CompletedTask;

        public Task NotifyMembershipRemovedAsync(Guid groupId, Guid userId) => Task.CompletedTask;

        public Task NotifyDevicesChangedAsync(Guid groupId, Guid affectedUserId, Guid deviceId)
        {
            Devices.Add(deviceId);
            return Task.CompletedTask;
        }
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
