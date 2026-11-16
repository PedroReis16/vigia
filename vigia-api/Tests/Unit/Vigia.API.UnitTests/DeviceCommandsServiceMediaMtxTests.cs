using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Vigia.API.Services.Devices;
using Vigia.Database.EFDao;
using Vigia.Fiware.Contracts;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Exceptions;

namespace Vigia.API.UnitTests;

public class DeviceCommandsServiceMediaMtxTests : IDisposable
{
    private readonly VigiaDbContext _context;
    private readonly RecordingFiware _fiware = new();
    private readonly DeviceCommandsService _service;
    private readonly Guid _deviceId = Guid.NewGuid();

    public DeviceCommandsServiceMediaMtxTests()
    {
        _context = CreateContext();
        Guid groupId = Guid.NewGuid();
        _context.Groups.Add(new Group
        {
            Id = groupId,
            OwnerId = Guid.NewGuid(),
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
        });
        _context.SaveChanges();

        DevicesDao devices = new(_context);
        IServiceScopeFactory scopes = new SingleScopeFactory(devices, _fiware);
        _service = new DeviceCommandsService(NullLogger<DeviceCommandsService>.Instance, scopes);
    }

    [Fact]
    public async Task SendDemandStartStreamingAsync_EnviaStart()
    {
        bool sent = await _service.SendDemandStartStreamingAsync(_deviceId);

        Assert.True(sent);
        Assert.Equal([("Vigia-0123abcd", DeviceCommands.START_STREAMING)], _fiware.Commands);
    }

    [Fact]
    public async Task SendUndemandStopStreamingAsync_EnviaStop()
    {
        bool sent = await _service.SendUndemandStopStreamingAsync(_deviceId);

        Assert.True(sent);
        Assert.Equal([("Vigia-0123abcd", DeviceCommands.STOP_STREAMING)], _fiware.Commands);
    }

    [Fact]
    public async Task SendDemandStartStreamingAsync_DeviceAusente_LancaValidacao()
    {
        EntityValidationException error = await Assert.ThrowsAsync<EntityValidationException>(
            () => _service.SendDemandStartStreamingAsync(Guid.NewGuid()));

        Assert.Equal(ErrorCodes.DEVICE_NOT_FOUND, error.ErrorCode);
        Assert.Empty(_fiware.Commands);
    }

    [Fact]
    public async Task SendUndemandStopStreamingAsync_FiwareRecusa_Lanca502()
    {
        _fiware.ReturnFalse = true;

        HttpResponseException error = await Assert.ThrowsAsync<HttpResponseException>(
            () => _service.SendUndemandStopStreamingAsync(_deviceId));

        Assert.Equal(StatusCodes.Status502BadGateway, error.StatusCode);
        Assert.Equal(ErrorCodes.FIWARE_COMMAND_FAILED, error.ErrorCode);
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

        public bool ReturnFalse { get; set; }

        public Task<bool> SendCommandAsync(string deviceName, DeviceCommands command, string? commandValue = null)
        {
            if (ReturnFalse)
                return Task.FromResult(false);

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
