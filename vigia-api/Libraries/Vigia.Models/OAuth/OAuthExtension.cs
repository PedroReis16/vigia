using System.IdentityModel.Tokens.Jwt;
using System.Text;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Authorization;
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

        services.AddAuthentication(options =>
            {
                options.DefaultScheme = JwtBearerDefaults.AuthenticationScheme;
            })
            .AddScheme<AuthenticationSchemeOptions, AllowAnonymousAuthenticationHandler>(
                AllowAnonymousDefaults.AllowAnonymousScheme, _ => { })
            .AddScheme<AuthenticationSchemeOptions, DeviceSignatureAuthenticationHandler>(
                DeviceSignatureDefaults.AuthenticationScheme, _ => { })
            .AddScheme<AuthenticationSchemeOptions, FrameAccessTokenAuthenticationHandler>(
                FrameAccessTokenDefaults.AuthenticationScheme, _ => { })
            .AddJwtBearer("OAuth", options =>
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
            })
            .AddPolicyScheme(JwtBearerDefaults.AuthenticationScheme, JwtBearerDefaults.AuthenticationScheme, options =>
            {
                options.ForwardDefaultSelector = context =>
                {
                    var remoteIpAddress = context.Connection.RemoteIpAddress?.ToString();
                    var localIpAddress = context.Connection.LocalIpAddress?.ToString();

                    bool canExternalUseAnonymous = true;

#if RELEASE
                    canExternalUseAnonymous = false;
#endif

                    string authHeader = context.Request.Headers.Authorization.ToString();

                    if (remoteIpAddress != null && authHeader.Contains($"Bearer {serviceSecretToken}"))
                    {
                        if (
                            canExternalUseAnonymous && Helpers.Validators.IsPrivateIpAddress(remoteIpAddress) ||
                            !canExternalUseAnonymous && remoteIpAddress.Equals(localIpAddress)
                        )
                            return AllowAnonymousDefaults.AllowAnonymousScheme;
                    }

                    return "OAuth";
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
}
