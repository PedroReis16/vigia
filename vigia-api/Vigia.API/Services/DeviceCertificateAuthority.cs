using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using Vigia.API.Contracts;
using Vigia.Database.Contracts;
using Vigia.Models.Contracts;

namespace Vigia.API.Services;

internal sealed class DeviceCertificateAuthority(
    IConfiguration configuration,
    IServiceScopeFactory scopeFactory) : IDeviceCertificateAuthority, IDeviceCertificateAuthenticator
{
    private readonly IConfiguration _configuration = configuration;
    private readonly IServiceScopeFactory _scopeFactory = scopeFactory;

    public bool RequireClientCertificate =>
        _configuration.GetValue<bool>("DeviceAuth:RequireClientCertificate");

    public IssuedDeviceCertificate Issue(Guid deviceId)
    {
        using X509Certificate2 ca = LoadCaCertificate();
        using ECDsa deviceKey = ECDsa.Create(ECCurve.NamedCurves.nistP256);
        CertificateRequest request = new($"CN={deviceId:D}", deviceKey, HashAlgorithmName.SHA256);
        request.CertificateExtensions.Add(new X509BasicConstraintsExtension(false, false, 0, true));
        request.CertificateExtensions.Add(new X509KeyUsageExtension(X509KeyUsageFlags.DigitalSignature, true));
        request.CertificateExtensions.Add(new X509SubjectKeyIdentifierExtension(request.PublicKey, false));

        byte[] serial = RandomNumberGenerator.GetBytes(16);
        serial[0] &= 0x7F;
        if (serial[0] == 0)
            serial[0] = 1;

        DateTimeOffset notBefore = DateTimeOffset.UtcNow.AddMinutes(-5);
        DateTimeOffset notAfter = DateTimeOffset.UtcNow.AddYears(2);
        using X509Certificate2 issued = request.Create(ca, notBefore, notAfter, serial);

        return new IssuedDeviceCertificate(
            issued.ExportCertificatePem(),
            deviceKey.ExportPkcs8PrivateKeyPem(),
            issued.SerialNumber.ToUpperInvariant(),
            notAfter.UtcDateTime);
    }

    public async Task<Guid?> AuthenticateAsync(
        string certificatePem,
        Guid? routeDeviceId,
        CancellationToken cancellationToken = default)
    {
        if (!TryReadCertificate(certificatePem, out X509Certificate2? certificate) || certificate is null)
            return null;

        using (certificate)
        {
            if (!HasValidChain(certificate))
                return null;

            if (!Guid.TryParse(certificate.GetNameInfo(X509NameType.SimpleName, false), out Guid subjectDeviceId))
                return null;

            if (routeDeviceId is Guid route && route != subjectDeviceId)
                return null;

            string serial = certificate.SerialNumber.ToUpperInvariant();
            using IServiceScope scope = _scopeFactory.CreateScope();
            IDevicesDao devices = scope.ServiceProvider.GetRequiredService<IDevicesDao>();

            if (routeDeviceId is Guid routeId)
            {
                Vigia.Models.Entities.Device? device = await devices.FindAsync(routeId);
                if (!SerialMatches(device, serial, subjectDeviceId))
                    return null;
                return subjectDeviceId;
            }

            Vigia.Models.Entities.Device? bySerial = await devices.FindByClientCertificateSerialAsync(serial, cancellationToken);
            if (!SerialMatches(bySerial, serial, subjectDeviceId))
                return null;
            return subjectDeviceId;
        }
    }

    private static bool SerialMatches(Vigia.Models.Entities.Device? device, string serial, Guid subjectDeviceId)
    {
        if (device is null || device.Id != subjectDeviceId)
            return false;
        if (string.IsNullOrWhiteSpace(device.ClientCertificateSerial))
            return false;
        if (!string.Equals(device.ClientCertificateSerial, serial, StringComparison.OrdinalIgnoreCase))
            return false;
        if (device.ClientCertificateNotAfter is DateTime notAfter && notAfter < DateTime.UtcNow)
            return false;
        return true;
    }

    private bool HasValidChain(X509Certificate2 certificate)
    {
        using X509Certificate2 ca = LoadCaCertificate();
        using X509Chain chain = new();
        chain.ChainPolicy.TrustMode = X509ChainTrustMode.CustomRootTrust;
        chain.ChainPolicy.CustomTrustStore.Add(ca);
        chain.ChainPolicy.RevocationMode = X509RevocationMode.NoCheck;
        return chain.Build(certificate);
    }

    private static bool TryReadCertificate(string pem, out X509Certificate2? certificate)
    {
        certificate = null;
        try
        {
            certificate = X509Certificate2.CreateFromPem(pem);
            return true;
        }
        catch (CryptographicException)
        {
            return false;
        }
    }

    private X509Certificate2 LoadCaCertificate()
    {
        string certificatePem = ReadMaterial("CaCertificatePem", "CaCertificatePath");
        string keyPem = ReadMaterial("CaPrivateKeyPem", "CaPrivateKeyPath");
        if (string.IsNullOrWhiteSpace(certificatePem) || string.IsNullOrWhiteSpace(keyPem))
            throw new InvalidOperationException("DeviceAuth CA certificate and private key are required.");

        return X509Certificate2.CreateFromPem(certificatePem, keyPem);
    }

    private string ReadMaterial(string pemKey, string pathKey)
    {
        string? pem = _configuration.GetValue<string>($"DeviceAuth:{pemKey}");
        if (!string.IsNullOrWhiteSpace(pem))
            return pem;

        string? path = _configuration.GetValue<string>($"DeviceAuth:{pathKey}");
        if (string.IsNullOrWhiteSpace(path) || !File.Exists(path))
            return string.Empty;

        return File.ReadAllText(path);
    }
}
