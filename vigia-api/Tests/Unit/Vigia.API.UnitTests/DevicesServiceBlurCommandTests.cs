using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Vigia.API.Models.DTOs.Devices;
using Vigia.API.Services.Devices;
using Vigia.Database.EFDao;
using Vigia.Fiware.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;

namespace Vigia.API.UnitTests;

public class DevicesServiceBlurCommandTests : IDisposable
{
    private readonly VigiaDbContext _context;
    private readonly RecordingFiware _fiware = new();
    private readonly DevicesService _service;
    private readonly Guid _ownerId = Guid.NewGuid();
    private readonly Guid _deviceId = Guid.NewGuid();

    public DevicesServiceBlurCommandTests()
    {
        _context = CreateContext();
        Guid groupId = Guid.NewGuid();
        _context.Groups.Add(new Group
        {
            Id = groupId,
            OwnerId = _ownerId,
            LinkedUsers = [],
            Devices = [],
        });
        _context.Devices.Add(new Device
        {
            Id = _deviceId,
            Name = "Vigia-0123abcd",
            MacAddress = "aa:bb:cc:dd:ee:ff",
            Nickname = "Sala",
            Room = DeviceRooms.LivingRoom,
            GroupId = groupId,
            IsBlurEnabled = false,
        });
        _context.SaveChanges();

        DevicesDao devices = new(_context);
        IServiceScopeFactory scopes = new SingleScopeFactory(devices, _fiware);
        _service = new DevicesService(
            NullLogger<DevicesService>.Instance,
            scopes,
            new ConfigurationBuilder().Build());
    }

    [Fact]
    public async Task UpdateDeviceAsync_IsBlurEnabled_EnviaComando()
    {
        await _service.UpdateDeviceAsync(_ownerId, _deviceId, new UpdateDeviceDTO { IsBlurEnabled = true });

        Assert.Equal([("Vigia-0123abcd", DeviceCommands.BLUR_ON)], _fiware.Commands);
        Device stored = await _context.Devices.SingleAsync(device => device.Id == _deviceId);
        Assert.True(stored.IsBlurEnabled);

        await _service.UpdateDeviceAsync(_ownerId, _deviceId, new UpdateDeviceDTO { IsBlurEnabled = false });

        Assert.Equal(DeviceCommands.BLUR_OFF, _fiware.Commands[1].Command);
        stored = await _context.Devices.SingleAsync(device => device.Id == _deviceId);
        Assert.False(stored.IsBlurEnabled);
    }

    [Fact]
    public async Task UpdateDeviceAsync_SoNickname_NaoEnviaComando()
    {
        await _service.UpdateDeviceAsync(_ownerId, _deviceId, new UpdateDeviceDTO { Nickname = "Quarto" });

        Assert.Empty(_fiware.Commands);
        Device stored = await _context.Devices.SingleAsync(device => device.Id == _deviceId);
        Assert.Equal("Quarto", stored.Nickname);
        Assert.False(stored.IsBlurEnabled);
    }

    [Fact]
    public async Task UpdateDeviceAsync_FalhaNoFiware_MantemPreferenciaGravada()
    {
        _fiware.FailSend = true;

        await _service.UpdateDeviceAsync(_ownerId, _deviceId, new UpdateDeviceDTO { IsBlurEnabled = true });

        Device stored = await _context.Devices.SingleAsync(device => device.Id == _deviceId);
        Assert.True(stored.IsBlurEnabled);
        Assert.Empty(_fiware.Commands);
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

    private sealed class RecordingFiware : IFiwareService
    {
        public List<(string DeviceName, DeviceCommands Command)> Commands { get; } = [];

        public bool FailSend { get; set; }

        public Task<bool> SendCommandAsync(string deviceName, DeviceCommands command, string? commandValue = null)
        {
            if (FailSend)
                throw new InvalidOperationException("fiware indisponível");

            Commands.Add((deviceName, command));
            return Task.FromResult(true);
        }

        public Task<bool> AddOrUpdateServiceAsync() => Task.FromResult(true);

        public Task<bool> SyncDevicesSchemaAsync() => Task.FromResult(true);

        public Task<bool> SyncSubscriptionsAsync() => Task.FromResult(true);

        public Task<bool> RegisterSensorAsync(Guid deviceId, string deviceName) => Task.FromResult(true);

        public Task<bool> EnsureDevicesProvisionedAsync(IReadOnlyCollection<(Guid DeviceId, string DeviceName)> devices) =>
            Task.FromResult(true);

        public Task<bool> EnsureSeedDeviceAsync() => Task.FromResult(true);

        public Task DeleteSensorAsync(Guid id, string name) => Task.CompletedTask;

        public Task<(List<Vigia.Fiware.Models.DeviceDTOs.IotAgentDeviceDTO> Devices, int TotalCount)> ListDevicesPageAsync(int offset, int limit) =>
            Task.FromResult((new List<Vigia.Fiware.Models.DeviceDTOs.IotAgentDeviceDTO>(), 0));
    }

    private sealed class SingleScopeFactory(params object[] services) : IServiceScopeFactory
    {
        public IServiceScope CreateScope() => new Scope(services);

        private sealed class Scope(object[] services) : IServiceScope
        {
            public IServiceProvider ServiceProvider { get; } = new Provider(services);

            public void Dispose()
            {
            }
        }

        private sealed class Provider(object[] services) : IServiceProvider
        {
            public object? GetService(Type serviceType) =>
                services.FirstOrDefault(service => serviceType.IsInstanceOfType(service));
        }
    }
}
