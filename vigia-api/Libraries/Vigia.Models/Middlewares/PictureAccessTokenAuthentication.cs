using System.Security.Claims;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Vigia.Models.Contracts;

namespace Vigia.Models.Middlewares;

public static class PictureAccessTokenDefaults
{
    public const string AuthenticationScheme = "PictureAccessToken";
    public const string QueryParameter = "accessToken";
}

public class PictureAccessTokenAuthenticationHandler(
    IOptionsMonitor<AuthenticationSchemeOptions> options,
    ILoggerFactory logger,
    UrlEncoder encoder,
    IPictureAccessTokenProvider pictureAccessTokenProvider) : AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder)
{
    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        string? accessToken = Request.Query[PictureAccessTokenDefaults.QueryParameter].FirstOrDefault();
        if (string.IsNullOrWhiteSpace(accessToken))
            return Task.FromResult(AuthenticateResult.Fail("accessToken ausente"));

        if (!Request.RouteValues.TryGetValue("id", out object? userIdValue) ||
            !Guid.TryParse(userIdValue?.ToString(), out Guid subjectUserId))
        {
            return Task.FromResult(AuthenticateResult.Fail("id inválido na rota"));
        }

        if (!pictureAccessTokenProvider.TryValidate(accessToken, subjectUserId, out Guid viewerId))
            return Task.FromResult(AuthenticateResult.Fail("accessToken inválido ou expirado"));

        Claim[] claims =
        [
            new(ClaimTypes.NameIdentifier, viewerId.ToString()),
            new("subject_user_id", subjectUserId.ToString()),
        ];

        ClaimsIdentity identity = new(claims, Scheme.Name);
        ClaimsPrincipal principal = new(identity);
        AuthenticationTicket ticket = new(principal, Scheme.Name);

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}
