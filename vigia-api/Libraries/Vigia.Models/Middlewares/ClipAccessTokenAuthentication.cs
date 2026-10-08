using System.Security.Claims;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Vigia.Models.Contracts;

namespace Vigia.Models.Middlewares;

public static class ClipAccessTokenDefaults
{
    public const string AuthenticationScheme = "ClipAccessToken";
    public const string QueryParameter = "accessToken";
}

public class ClipAccessTokenAuthenticationHandler(
    IOptionsMonitor<AuthenticationSchemeOptions> options,
    ILoggerFactory logger,
    UrlEncoder encoder,
    IClipAccessTokenProvider clipAccessTokenProvider) : AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder)
{
    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        string? accessToken = Request.Query[ClipAccessTokenDefaults.QueryParameter].FirstOrDefault();
        if (string.IsNullOrWhiteSpace(accessToken))
            return Task.FromResult(AuthenticateResult.Fail("accessToken ausente"));

        if (!Request.RouteValues.TryGetValue("deviceId", out object? deviceIdValue) ||
            !Guid.TryParse(deviceIdValue?.ToString(), out Guid deviceId))
        {
            return Task.FromResult(AuthenticateResult.Fail("deviceId inválido na rota"));
        }

        if (!clipAccessTokenProvider.TryValidate(accessToken, deviceId, out Guid userId))
            return Task.FromResult(AuthenticateResult.Fail("accessToken inválido ou expirado"));

        Claim[] claims =
        [
            new(ClaimTypes.NameIdentifier, userId.ToString()),
            new("device_id", deviceId.ToString()),
        ];

        ClaimsIdentity identity = new(claims, Scheme.Name);
        ClaimsPrincipal principal = new(identity);
        AuthenticationTicket ticket = new(principal, Scheme.Name);

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}
