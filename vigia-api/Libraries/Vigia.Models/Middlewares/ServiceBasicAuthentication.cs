using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace Vigia.Models.Middlewares;

public static class ServiceBasicDefaults
{
    public const string AuthenticationScheme = "ServiceBasic";
    public const string OrionRole = "orion";
    public const string MediaMtxRole = "mediamtx";
}

public readonly record struct ServiceBasicAccount(string Username, string Password);

public static class ServiceBasicCredentials
{
    public static string? Match(string username, string password, ServiceBasicAccount orion, ServiceBasicAccount mediaMtx)
    {
        bool orionMatch = Matches(username, password, orion, ServiceBasicDefaults.OrionRole);
        bool mediaMtxMatch = Matches(username, password, mediaMtx, ServiceBasicDefaults.MediaMtxRole);
        if (orionMatch)
            return ServiceBasicDefaults.OrionRole;
        if (mediaMtxMatch)
            return ServiceBasicDefaults.MediaMtxRole;
        return null;
    }

    private static bool Matches(string username, string password, ServiceBasicAccount account, string fallbackUsername)
    {
        if (string.IsNullOrEmpty(account.Password))
            return false;

        string expectedUser = string.IsNullOrWhiteSpace(account.Username) ? fallbackUsername : account.Username;
        return FixedTimeEquals(username, expectedUser) && FixedTimeEquals(password, account.Password);
    }

    public static bool FixedTimeEquals(string left, string right)
    {
        byte[] leftBytes = Encoding.UTF8.GetBytes(left);
        byte[] rightBytes = Encoding.UTF8.GetBytes(right);
        return leftBytes.Length == rightBytes.Length && CryptographicOperations.FixedTimeEquals(leftBytes, rightBytes);
    }
}

public class ServiceBasicAuthenticationHandler(
    IOptionsMonitor<AuthenticationSchemeOptions> options,
    ILoggerFactory logger,
    UrlEncoder encoder,
    IConfiguration configuration) : AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder)
{
    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        string? header = Request.Headers.Authorization.ToString();
        if (string.IsNullOrWhiteSpace(header) ||
            !header.StartsWith("Basic ", StringComparison.OrdinalIgnoreCase))
        {
            return Task.FromResult(AuthenticateResult.Fail("Basic ausente"));
        }

        string encoded = header["Basic ".Length..].Trim();
        string decoded;
        try
        {
            decoded = Encoding.UTF8.GetString(Convert.FromBase64String(encoded));
        }
        catch (FormatException)
        {
            return Task.FromResult(AuthenticateResult.Fail("Basic inválido"));
        }

        int separator = decoded.IndexOf(':');
        if (separator <= 0)
            return Task.FromResult(AuthenticateResult.Fail("Basic inválido"));

        string username = decoded[..separator];
        string password = decoded[(separator + 1)..];
        string? role = ServiceBasicCredentials.Match(username, password, ReadAccount("Orion"), ReadAccount("MediaMtx"));
        if (role is null)
            return Task.FromResult(AuthenticateResult.Fail("Credencial Basic inválida"));

        Claim[] claims =
        [
            new(ClaimTypes.Name, username),
            new(ClaimTypes.NameIdentifier, role),
            new(ClaimTypes.Role, role),
        ];

        ClaimsIdentity identity = new(claims, Scheme.Name);
        return Task.FromResult(AuthenticateResult.Success(new AuthenticationTicket(new ClaimsPrincipal(identity), Scheme.Name)));
    }

    private ServiceBasicAccount ReadAccount(string name)
    {
        IConfigurationSection section = configuration.GetSection($"ServiceBasic:{name}");
        return new ServiceBasicAccount(
            section.GetValue<string>("Username") ?? string.Empty,
            section.GetValue<string>("Password") ?? string.Empty);
    }
}
