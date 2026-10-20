using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Vigia.API.Services.Devices;
using Vigia.Database.EFDao;
using Vigia.Models.Contracts;
using Vigia.Models.Entities;

namespace Vigia.API.UnitTests;

public class DeviceUsersServiceProfileTests : IDisposable
{
    private readonly VigiaDbContext _context;
    private readonly DeviceUsersService _service;
    private readonly Guid _ownerId = Guid.NewGuid();
    private readonly Guid _guestId = Guid.NewGuid();
    private readonly Guid _deviceId = Guid.NewGuid();

    public DeviceUsersServiceProfileTests()
    {
        _context = CreateContext();
        Guid groupId = Guid.NewGuid();
        User owner = new()
        {
            Id = _ownerId,
            FirstName = "Ana",
            LastName = "Lima",
            Email = "ana@vigia.test",
            Phone = "1",
            PictureKey = $"users/{_ownerId:D}/avatar",
            LinkedGroups = [],
        };
        User guest = new()
        {
            Id = _guestId,
            Email = "guest@vigia.test",
            Phone = "2",
            LinkedGroups = [],
        };
        Group group = new()
        {
            Id = groupId,
            OwnerId = _ownerId,
            LinkedUsers = [owner, guest],
            Devices = [],
        };
        owner.LinkedGroups.Add(group);
        guest.LinkedGroups.Add(group);
        _context.Groups.Add(group);
        _context.Devices.Add(new Device
        {
            Id = _deviceId,
            Name = "Vigia-0123abcd",
            MacAddress = "aa:bb:cc:dd:ee:ff",
            GroupId = groupId,
        });
        _context.SaveChanges();

        IServiceScopeFactory scopes = new ScopeFactory(
            new DevicesDao(_context),
            new GroupDao(_context),
            new UserDao(_context));
        _service = new DeviceUsersService(
            NullLogger<DeviceUsersService>.Instance,
            scopes,
            new FixedPictureAccess());
    }

    [Fact]
    public async Task GetDeviceUsersAsync_ReturnsDisplayNameAndPictureUrl()
    {
        var users = await _service.GetDeviceUsersAsync(_deviceId, _ownerId);

        var owner = Assert.Single(users, user => user.Id == _ownerId);
        var guest = Assert.Single(users, user => user.Id == _guestId);
        Assert.Equal("Ana Lima", owner.Name);
        Assert.NotNull(owner.UserPictureUrl);
        Assert.Contains($"users/{_ownerId:D}/picture?accessToken=", owner.UserPictureUrl);
        Assert.Contains($"{_ownerId:N}-{_ownerId:N}", owner.UserPictureUrl);
        Assert.Equal("guest@vigia.test", guest.Name);
        Assert.Null(guest.UserPictureUrl);
    }

    [Fact]
    public async Task GetDeviceUsersAsync_OutsiderIsRejected()
    {
        await Assert.ThrowsAsync<UnauthorizedAccessException>(
            () => _service.GetDeviceUsersAsync(_deviceId, Guid.NewGuid()));
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

    private sealed class FixedPictureAccess : IPictureAccessTokenProvider
    {
        public string IssueToken(Guid viewerId, Guid subjectUserId) => $"{viewerId:N}-{subjectUserId:N}";

        public bool TryValidate(string token, Guid subjectUserId, out Guid viewerId)
        {
            viewerId = Guid.Empty;
            return false;
        }
    }

    private sealed class ScopeFactory(params object[] services) : IServiceScopeFactory
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
