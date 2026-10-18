using System.Security.Claims;
using System.Security.Cryptography.X509Certificates;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Vigia.Models.Contracts;

namespace Vigia.Models.Middlewares;

public static class DeviceCertificateDefaults
{
    public const string AuthenticationScheme = "DeviceCertificate";
    public const string ForwardedCertificateHeader = "X-Forwarded-Tls-Client-Cert";
}

public class DeviceCertificateAuthenticationHandler(
    IOptionsMonitor<AuthenticationSchemeOptions> options,
    ILoggerFactory logger,
    UrlEncoder encoder,
    IDeviceCertificateAuthenticator authenticator) : AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder)
{
    protected override async Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        string? pem = ReadCertificatePem();
        if (string.IsNullOrWhiteSpace(pem))
            return AuthenticateResult.Fail("Certificado de cliente ausente");

        Guid? routeDeviceId = null;
        if (Request.RouteValues.TryGetValue("deviceId", out object? deviceIdValue) &&
            Guid.TryParse(deviceIdValue?.ToString(), out Guid parsed))
        {
            routeDeviceId = parsed;
        }

        Guid? deviceId = await authenticator.AuthenticateAsync(pem, routeDeviceId, Context.RequestAborted);
        if (deviceId is null)
            return AuthenticateResult.Fail("Certificado de cliente inválido");

        Claim[] claims =
        [
            new(ClaimTypes.NameIdentifier, deviceId.Value.ToString()),
            new("device_id", deviceId.Value.ToString()),
            new(ClaimTypes.Role, "device"),
        ];

        ClaimsIdentity identity = new(claims, Scheme.Name);
        return AuthenticateResult.Success(new AuthenticationTicket(new ClaimsPrincipal(identity), Scheme.Name));
    }

    private string? ReadCertificatePem()
    {
        if (Request.Headers.TryGetValue(DeviceCertificateDefaults.ForwardedCertificateHeader, out var forwarded) &&
            !string.IsNullOrWhiteSpace(forwarded.ToString()))
        {
            string first = forwarded.ToString().Split(',')[0].Trim();
            return Uri.UnescapeDataString(first);
        }

        return Context.Connection.ClientCertificate?.ExportCertificatePem();
    }
}

/// <summary>
/// Exige o certificado de cliente quando <c>DeviceAuth:RequireClientCertificate</c> está ligado.
/// Com a flag desligada, a ação segue anônima.
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class)]
public sealed class DeviceCertificateAttribute : Attribute, IAsyncAuthorizationFilter
{
    public async Task OnAuthorizationAsync(AuthorizationFilterContext context)
    {
        IConfiguration configuration = context.HttpContext.RequestServices.GetRequiredService<IConfiguration>();
        if (!configuration.GetValue<bool>("DeviceAuth:RequireClientCertificate"))
            return;

        AuthenticateResult result = await context.HttpContext.AuthenticateAsync(DeviceCertificateDefaults.AuthenticationScheme);
        if (!result.Succeeded || result.Principal is null)
        {
            context.Result = new UnauthorizedResult();
            return;
        }

        context.HttpContext.User = result.Principal;
    }
}
