using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using NSec.Cryptography;
using Vigia.Models.Contracts;

namespace Vigia.Models.Middlewares;

public static class DeviceSignatureDefaults
{
    public const string AuthenticationScheme = "DeviceSignature";
    public const string TimestampHeader = "X-Device-Timestamp";
    public const string SignatureHeader = "X-Device-Signature";
    public static readonly TimeSpan MaxClockSkew = TimeSpan.FromSeconds(60);
}

public class DeviceSignatureAuthenticationHandler(
    IOptionsMonitor<AuthenticationSchemeOptions> options,
    ILoggerFactory logger,
    UrlEncoder encoder,
    IDeviceSignPublicKeyProvider signPublicKeyProvider) : AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder)
{
    protected override async Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.TryGetValue(DeviceSignatureDefaults.TimestampHeader, out var timestampValues) ||
            !long.TryParse(timestampValues.FirstOrDefault(), out long timestampUnix))
        {
            return AuthenticateResult.Fail("Timestamp do dispositivo ausente ou inválido");
        }

        if (!Request.Headers.TryGetValue(DeviceSignatureDefaults.SignatureHeader, out var signatureValues) ||
            string.IsNullOrWhiteSpace(signatureValues.FirstOrDefault()))
        {
            return AuthenticateResult.Fail("Assinatura do dispositivo ausente");
        }

        string signatureHex = signatureValues.ToString();

        DateTimeOffset timestamp = DateTimeOffset.FromUnixTimeSeconds(timestampUnix);
        if (Math.Abs((DateTimeOffset.UtcNow - timestamp).TotalSeconds) > DeviceSignatureDefaults.MaxClockSkew.TotalSeconds)
            return AuthenticateResult.Fail("Timestamp do dispositivo fora da janela permitida");

        if (!Request.RouteValues.TryGetValue("deviceId", out object? deviceIdValue) ||
            !Guid.TryParse(deviceIdValue?.ToString(), out Guid deviceId))
        {
            return AuthenticateResult.Fail("deviceId inválido na rota");
        }

        string? signPublicKeyHex = await signPublicKeyProvider.GetSignPublicKeyAsync(deviceId);
        if (string.IsNullOrWhiteSpace(signPublicKeyHex))
            return AuthenticateResult.Fail("Chave pública do dispositivo não encontrada");

        Request.EnableBuffering();

        byte[] bodyBytes;
        using (MemoryStream buffer = new())
        {
            await Request.Body.CopyToAsync(buffer);
            bodyBytes = buffer.ToArray();
            Request.Body.Position = 0;
        }

        string bodyHashHex = Convert.ToHexString(SHA256.HashData(bodyBytes)).ToLowerInvariant();
        string canonical =
            $"POST\n/devices/{deviceId}/frame\n{timestampUnix}\n{bodyHashHex}";

        byte[] message = Encoding.UTF8.GetBytes(canonical);

        try
        {
            byte[] publicKeyBytes = Convert.FromHexString(signPublicKeyHex);
            byte[] signatureBytes = Convert.FromHexString(signatureHex);

            PublicKey publicKey = PublicKey.Import(
                SignatureAlgorithm.Ed25519,
                publicKeyBytes,
                KeyBlobFormat.RawPublicKey);

            if (!SignatureAlgorithm.Ed25519.Verify(publicKey, message, signatureBytes))
                return AuthenticateResult.Fail("Assinatura do dispositivo inválida");
        }
        catch (Exception)
        {
            return AuthenticateResult.Fail("Falha ao validar assinatura do dispositivo");
        }

        Claim[] claims =
        [
            new("device_id", deviceId.ToString()),
            new(ClaimTypes.NameIdentifier, deviceId.ToString()),
        ];

        ClaimsIdentity identity = new(claims, Scheme.Name);
        ClaimsPrincipal principal = new(identity);
        AuthenticationTicket ticket = new(principal, Scheme.Name);

        return AuthenticateResult.Success(ticket);
    }
}
