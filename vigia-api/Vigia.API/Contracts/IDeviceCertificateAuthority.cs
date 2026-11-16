namespace Vigia.API.Contracts;

public interface IDeviceCertificateAuthority
{
    bool RequireClientCertificate { get; }

    IssuedDeviceCertificate Issue(Guid deviceId);
}

public sealed record IssuedDeviceCertificate(
    string CertificatePem,
    string PrivateKeyPem,
    string SerialNumber,
    DateTime NotAfterUtc);
