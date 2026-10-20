using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Vigia.API.Contracts;
using Vigia.API.Models.DTOs.Devices;
using Vigia.API.Services;
using Vigia.API.Services.Devices;
using Vigia.Database.Contracts;
using Vigia.Database.EFDao;
using Vigia.Fiware.Contracts;
using IotAgentDeviceDTO = Vigia.Fiware.Models.DeviceDTOs.IotAgentDeviceDTO;
using Vigia.Models.Entities;
using Vigia.Models.Enums;
using Vigia.Models.Middlewares;

namespace Vigia.API.UnitTests;

public class DeviceCertificateAuthorityTests : IDisposable
{
    private readonly VigiaDbContext _context = CreateContext();

    [Fact]
    public async Task Authenticate_AceitaCertificadoDoDeviceNaRota()
    {
        (DeviceCertificateAuthority authority, Guid deviceId) = await IssueForStoredDeviceAsync();
        IssuedDeviceCertificate issued = authority.Issue(deviceId);
        await new DevicesDao(_context).UpdateClientCertificateAsync(deviceId, issued.SerialNumber, issued.NotAfterUtc);

        Guid? authenticated = await authority.AuthenticateAsync(issued.CertificatePem, deviceId);

        Assert.Equal(deviceId, authenticated);
    }

    [Fact]
    public async Task Authenticate_RejeitaRotaDeOutroDevice()
    {
        (DeviceCertificateAuthority authority, Guid deviceId) = await IssueForStoredDeviceAsync();
        IssuedDeviceCertificate issued = authority.Issue(deviceId);
        await new DevicesDao(_context).UpdateClientCertificateAsync(deviceId, issued.SerialNumber, issued.NotAfterUtc);

        Guid? authenticated = await authority.AuthenticateAsync(issued.CertificatePem, Guid.NewGuid());

        Assert.Null(authenticated);
    }

    [Fact]
    public async Task Authenticate_RejeitaSerialRevogado()
    {
        (DeviceCertificateAuthority authority, Guid deviceId) = await IssueForStoredDeviceAsync();
        IssuedDeviceCertificate issued = authority.Issue(deviceId);
        await new DevicesDao(_context).UpdateClientCertificateAsync(deviceId, "REVOKED", issued.NotAfterUtc);

        Guid? authenticated = await authority.AuthenticateAsync(issued.CertificatePem, deviceId);

        Assert.Null(authenticated);
    }

    [Fact]
    public async Task Register_EmiteNoPrimeiroRegistroERotacionaSoParaODono()
    {
        Guid deviceId = Guid.NewGuid();
        Guid ownerId = Guid.NewGuid();
        DeviceCertificateAuthority authority = CreateAuthority();
        DevicesService service = CreateService(authority);

        DeviceClientCertificateDTO? created = await service.RegisterDeviceAsync(
            new NewDeviceDTO(deviceId, "Vigia-a1b2c3d4", "aa:bb:cc:dd:ee:01"),
            ownerId);

        Assert.False(string.IsNullOrWhiteSpace(created?.Certificate));
        string firstSerial = (await _context.Devices.SingleAsync(device => device.Id == deviceId)).ClientCertificateSerial!;

        Guid groupId = Guid.NewGuid();
        _context.Groups.Add(new Group
        {
            Id = groupId,
            OwnerId = ownerId,
            LinkedUsers = [],
            Devices = [],
        });
        await _context.SaveChangesAsync();
        Device stored = await _context.Devices.SingleAsync(device => device.Id == deviceId);
        stored.GroupId = groupId;
        await _context.SaveChangesAsync();
        _context.ChangeTracker.Clear();

        DeviceClientCertificateDTO? rotated = await service.RegisterDeviceAsync(
            new NewDeviceDTO(deviceId, "Vigia-a1b2c3d4", "aa:bb:cc:dd:ee:01"),
            ownerId);

        Assert.NotEqual(created!.PrivateKey, rotated!.PrivateKey);
        string secondSerial = (await _context.Devices.AsNoTracking().SingleAsync(device => device.Id == deviceId)).ClientCertificateSerial!;
        Assert.NotEqual(firstSerial, secondSerial);

        await Assert.ThrowsAsync<UnauthorizedAccessException>(() => service.RegisterDeviceAsync(
            new NewDeviceDTO(deviceId, "Vigia-a1b2c3d4", "aa:bb:cc:dd:ee:01"),
            Guid.NewGuid()));
    }

    [Fact]
    public void ServiceBasic_RejeitaSenhaAusenteEContaTrocada()
    {
        ServiceBasicAccount orion = new("orion", "dev-orion-password");
        ServiceBasicAccount mediaMtx = new("mediamtx", "");

        Assert.Equal(ServiceBasicDefaults.OrionRole, ServiceBasicCredentials.Match("orion", "dev-orion-password", orion, mediaMtx));
        Assert.Null(ServiceBasicCredentials.Match("mediamtx", "dev-mediamtx-password", orion, mediaMtx));
        Assert.Null(ServiceBasicCredentials.Match("orion", "outra", orion, mediaMtx));
    }

    public void Dispose() => _context.Dispose();

    private async Task<(DeviceCertificateAuthority Authority, Guid DeviceId)> IssueForStoredDeviceAsync()
    {
        Guid deviceId = Guid.NewGuid();
        _context.Devices.Add(new Device
        {
            Id = deviceId,
            Name = "Vigia-a1b2c3d4",
            MacAddress = "aa:bb:cc:dd:ee:01",
        });
        await _context.SaveChangesAsync();
        return (CreateAuthority(), deviceId);
    }

    private DeviceCertificateAuthority CreateAuthority()
    {
        (string certificate, string key) = CreateCa();
        IConfiguration configuration = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
        {
            ["DeviceAuth:RequireClientCertificate"] = "true",
            ["DeviceAuth:CaCertificatePem"] = certificate,
            ["DeviceAuth:CaPrivateKeyPem"] = key,
        }).Build();
        return new DeviceCertificateAuthority(configuration, new ScopeFactory(_context));
    }

    private DevicesService CreateService(DeviceCertificateAuthority authority)
    {
        IConfiguration configuration = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
        {
            ["DeviceAuth:RequireClientCertificate"] = "true",
        }).Build();
        return new DevicesService(
            NullLogger<DevicesService>.Instance,
            new ScopeFactory(_context),
            configuration,
            authority);
    }

    private static (string Certificate, string Key) CreateCa()
    {
        using ECDsa key = ECDsa.Create(ECCurve.NamedCurves.nistP256);
        CertificateRequest request = new("CN=Vigia Test CA", key, HashAlgorithmName.SHA256);
        request.CertificateExtensions.Add(new X509BasicConstraintsExtension(true, false, 0, true));
        request.CertificateExtensions.Add(new X509SubjectKeyIdentifierExtension(request.PublicKey, false));
        using X509Certificate2 certificate = request.CreateSelfSigned(
            DateTimeOffset.UtcNow.AddDays(-1),
            DateTimeOffset.UtcNow.AddYears(5));
        return (certificate.ExportCertificatePem(), key.ExportPkcs8PrivateKeyPem());
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

    private sealed class ScopeFactory(VigiaDbContext context) : IServiceScopeFactory
    {
        public IServiceScope CreateScope() => new Scope(new DevicesDao(context), new StubFiware());

        private sealed class Scope(DevicesDao devices, StubFiware fiware) : IServiceScope
        {
            public IServiceProvider ServiceProvider { get; } = new Provider(devices, fiware);

            public void Dispose()
            {
            }
        }

        private sealed class Provider(DevicesDao devices, StubFiware fiware) : IServiceProvider
        {
            public object? GetService(Type serviceType)
            {
                if (serviceType == typeof(IDevicesDao))
                    return devices;
                if (serviceType == typeof(IFiwareService))
                    return fiware;
                return null;
            }
        }
    }

    private sealed class StubFiware : IFiwareService
    {
        public Task<bool> AddOrUpdateServiceAsync() => Task.FromResult(true);
        public Task<bool> SyncDevicesSchemaAsync() => Task.FromResult(true);
        public Task<bool> SyncSubscriptionsAsync() => Task.FromResult(true);
        public Task<bool> RegisterSensorAsync(Guid deviceId, string deviceName) => Task.FromResult(true);
        public Task<bool> EnsureDevicesProvisionedAsync(IReadOnlyCollection<(Guid DeviceId, string DeviceName)> devices) => Task.FromResult(true);
        public Task<bool> EnsureSeedDeviceAsync() => Task.FromResult(true);
        public Task DeleteSensorAsync(Guid id, string name) => Task.CompletedTask;
        public Task<bool> SendCommandAsync(string deviceName, DeviceCommands command, string? commandValue = null) => Task.FromResult(true);
        public Task<(List<IotAgentDeviceDTO> Devices, int TotalCount)> ListDevicesPageAsync(int offset, int limit) =>
            Task.FromResult((new List<IotAgentDeviceDTO>(), 0));
    }
}
