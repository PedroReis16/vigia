namespace Vigia.Models.Contracts;

public interface IDeviceCertificateAuthenticator
{
    Task<Guid?> AuthenticateAsync(string certificatePem, Guid? routeDeviceId, CancellationToken cancellationToken = default);
}
