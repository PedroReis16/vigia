using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text.Encodings.Web;
using Vigia.Models.DTOs;

namespace Vigia.Models.Middlewares;

public class AllowAnonymousAuthenticationHandler(
    IOptionsMonitor<AuthenticationSchemeOptions> options,
    ILoggerFactory logger,
    UrlEncoder encoder) : AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder)
{
    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        var claims = new[]
        {
            new Claim(JwtRegisteredClaimNames.Sub, new Guid("05ae0d5a-5ef8-44c4-a6de-df0725cdd39b").ToString()),
            new Claim(ClaimTypes.NameIdentifier, "anonymous"),
            new Claim(ClaimTypes.Role, ServiceRoles.ADMIN),
        };
        var identity = new ClaimsIdentity(claims, Scheme.Name);
        var principal = new ClaimsPrincipal(identity);
        var ticket = new AuthenticationTicket(principal, Scheme.Name);

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}

public class AllowAnonymousDefaults
{
    public const string AllowAnonymousScheme = "AllowAnonymous";
}
