using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace Vigia.Models.Middlewares;

public static class MediaMtxTokenDefaults
{
    public const string AuthenticationScheme = "MediaMtxToken";
    public const string TokenHeader = "X-MediaMTX-Token";
    public const string ConfigSection = "MediaMTX";
    public const string ConfigTokenKey = "WebhookToken";
}

public class MediaMtxTokenAuthenticationHandler(
    IOptionsMonitor<AuthenticationSchemeOptions> options,
    ILoggerFactory logger,
    UrlEncoder encoder,
    IConfiguration configuration) : AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder)
{
    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        string? expectedToken = configuration
            .GetSection(MediaMtxTokenDefaults.ConfigSection)
            .GetValue<string>(MediaMtxTokenDefaults.ConfigTokenKey);

        if (string.IsNullOrWhiteSpace(expectedToken))
            return Task.FromResult(AuthenticateResult.Fail("MediaMTX:WebhookToken não configurado"));

        if (!Request.Headers.TryGetValue(MediaMtxTokenDefaults.TokenHeader, out var tokenValues) ||
            string.IsNullOrWhiteSpace(tokenValues.FirstOrDefault()))
        {
            return Task.FromResult(AuthenticateResult.Fail("Token MediaMTX ausente"));
        }

        string providedToken = tokenValues.ToString();
        if (!FixedTimeEquals(providedToken, expectedToken))
            return Task.FromResult(AuthenticateResult.Fail("Token MediaMTX inválido"));

        Claim[] claims =
        [
            new(ClaimTypes.Name, "mediamtx"),
            new(ClaimTypes.NameIdentifier, "mediamtx"),
            new("role", "system"),
        ];

        ClaimsIdentity identity = new(claims, Scheme.Name);
        ClaimsPrincipal principal = new(identity);
        AuthenticationTicket ticket = new(principal, Scheme.Name);

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }

    private static bool FixedTimeEquals(string a, string b)
    {
        byte[] aBytes = Encoding.UTF8.GetBytes(a);
        byte[] bBytes = Encoding.UTF8.GetBytes(b);
        return aBytes.Length == bBytes.Length && CryptographicOperations.FixedTimeEquals(aBytes, bBytes);
    }
}
