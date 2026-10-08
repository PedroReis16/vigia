using System.IdentityModel.Tokens.Jwt;
using System.Text;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.IdentityModel.Tokens;
using Vigia.Models.Middlewares;
using Vigia.Models.OAuth;

namespace Vigia.Models.Extensions;

public static class OAuthExtension
{
    public static IServiceCollection ConfigureOAuth(this IServiceCollection services, IConfiguration configuration)
    {
        string secretKey = configuration.GetValue<string>("JWT:SecretKey")
            ?? throw new InvalidOperationException("JWT:SecretKey is required");
        string issuer = configuration.GetValue<string>("JWT:Issuer")
            ?? throw new InvalidOperationException("JWT:Issuer is required");
        string audience = configuration.GetValue<string>("JWT:Audience")
            ?? throw new InvalidOperationException("JWT:Audience is required");

        string serviceSecretToken = configuration
            .GetSection(OAuthConstants.SECRET_SECTION)
            .GetValue<string>(OAuthConstants.SECRET_SERVICE_TOKEN) ?? string.Empty;

        string? keycloakMetadata = configuration.GetValue<string>("Keycloak:MetadataAddress");
        string? keycloakIssuer = configuration.GetValue<string>("Keycloak:ValidIssuer");
        string? keycloakAudience = configuration.GetValue<string>("Keycloak:Audience");
        bool keycloakEnabled = !string.IsNullOrWhiteSpace(keycloakMetadata)
            && !string.IsNullOrWhiteSpace(keycloakIssuer)
            && !string.IsNullOrWhiteSpace(keycloakAudience);

        AuthenticationBuilder authBuilder = services.AddAuthentication(options =>
            {
                options.DefaultScheme = JwtBearerDefaults.AuthenticationScheme;
            })
            .AddScheme<AuthenticationSchemeOptions, AllowAnonymousAuthenticationHandler>(
                AllowAnonymousDefaults.AllowAnonymousScheme, _ => { })
            .AddScheme<AuthenticationSchemeOptions, FrameAccessTokenAuthenticationHandler>(
                FrameAccessTokenDefaults.AuthenticationScheme, _ => { })
            .AddScheme<AuthenticationSchemeOptions, ClipAccessTokenAuthenticationHandler>(
                ClipAccessTokenDefaults.AuthenticationScheme, _ => { })
            .AddScheme<AuthenticationSchemeOptions, MediaMtxTokenAuthenticationHandler>(
                MediaMtxTokenDefaults.AuthenticationScheme, _ => { })
            .AddJwtBearer(BearerSchemeSelector.LocalJwtScheme, options =>
            {
                options.MapInboundClaims = false;
                options.TokenValidationParameters = new TokenValidationParameters
                {
                    ValidateIssuerSigningKey = true,
                    IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey)),
                    ValidateIssuer = true,
                    ValidIssuer = issuer,
                    ValidateAudience = true,
                    ValidAudience = audience,
                    ValidateLifetime = true,
                    ClockSkew = TimeSpan.FromSeconds(30),
                    RoleClaimType = "role",
                    NameClaimType = JwtRegisteredClaimNames.Sub,
                };
                options.Events = new JwtBearerEvents
                {
                    OnMessageReceived = ReadSignalRAccessToken,
                };
            });

        if (keycloakEnabled)
        {
            authBuilder.AddJwtBearer(BearerSchemeSelector.KeycloakScheme, options =>
            {
                options.MapInboundClaims = false;
                options.RequireHttpsMetadata = false;
                options.MetadataAddress = keycloakMetadata!;
                options.TokenValidationParameters = new TokenValidationParameters
                {
                    ValidateIssuerSigningKey = true,
                    ValidateIssuer = true,
                    ValidIssuer = keycloakIssuer,
                    ValidateAudience = true,
                    ValidAudience = keycloakAudience,
                    ValidateLifetime = true,
                    ClockSkew = TimeSpan.FromSeconds(30),
                    NameClaimType = JwtRegisteredClaimNames.Sub,
                    // Discovery inside Docker reports the internal issuer. Accept only the public one.
                    IssuerValidator = (tokenIssuer, _, _) =>
                    {
                        if (string.Equals(tokenIssuer, keycloakIssuer, StringComparison.Ordinal))
                            return tokenIssuer;

                        throw new SecurityTokenInvalidIssuerException(
                            $"Issuer '{tokenIssuer}' does not match '{keycloakIssuer}'.");
                    },
                };
                options.Events = new JwtBearerEvents
                {
                    OnMessageReceived = ReadSignalRAccessToken,
                };
            });
        }

        authBuilder.AddPolicyScheme(JwtBearerDefaults.AuthenticationScheme, JwtBearerDefaults.AuthenticationScheme, options =>
        {
            options.ForwardDefaultSelector = context =>
            {
                // Test/dev bypass: Bearer {OAuth:ServiceToken} → ADMIN principal
                if (!string.IsNullOrEmpty(serviceSecretToken) &&
                    TryResolveServiceTokenAsAdmin(context, serviceSecretToken))
                {
                    return AllowAnonymousDefaults.AllowAnonymousScheme;
                }

                string? hubAccessToken = null;
                PathString path = context.Request.Path;
                if (path.StartsWithSegments("/hubs") ||
                    path.Value?.Contains("/hubs/", StringComparison.OrdinalIgnoreCase) == true)
                {
                    hubAccessToken = context.Request.Query["access_token"];
                }

                return BearerSchemeSelector.Select(
                    context.Request.Headers.Authorization.ToString(),
                    hubAccessToken,
                    keycloakEnabled ? keycloakIssuer : null);
            };
        });

        services.AddAuthorization(options =>
        {
            options.FallbackPolicy = new AuthorizationPolicyBuilder()
                .RequireAuthenticatedUser()
                .Build();
        });

        return services;
    }

    /// <summary>
    /// SignalR WebSockets cannot send Authorization headers; the token arrives as a query value.
    /// PathBase may leave Path as "/hubs/..." or include a negotiate suffix.
    /// </summary>
    private static Task ReadSignalRAccessToken(MessageReceivedContext context)
    {
        string? accessToken = context.Request.Query["access_token"];
        PathString path = context.HttpContext.Request.Path;
        if (!string.IsNullOrEmpty(accessToken) &&
            (path.StartsWithSegments("/hubs") ||
             path.Value?.Contains("/hubs/", StringComparison.OrdinalIgnoreCase) == true))
        {
            context.Token = accessToken;
        }

        return Task.CompletedTask;
    }

    /// <summary>
    /// Returns true when the request carries the fixed service token and originates
    /// from an allowed network (private IPs in non-RELEASE; loopback-only in RELEASE).
    /// </summary>
    private static bool TryResolveServiceTokenAsAdmin(HttpContext context, string serviceSecretToken)
    {
        string authHeader = context.Request.Headers.Authorization.ToString();
        if (!authHeader.Equals($"Bearer {serviceSecretToken}", StringComparison.Ordinal))
            return false;

        string? remoteIpAddress = context.Connection.RemoteIpAddress?.ToString();
        if (remoteIpAddress is null)
            return false;

#if RELEASE
        string? localIpAddress = context.Connection.LocalIpAddress?.ToString();
        return remoteIpAddress.Equals(localIpAddress, StringComparison.Ordinal);
#else
        return Helpers.Validators.IsPrivateIpAddress(remoteIpAddress);
#endif
    }
}
