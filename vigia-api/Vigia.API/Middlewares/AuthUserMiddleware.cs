using System.Text.Json;
using Vigia.API.Contracts.CacheServices;
using Vigia.API.Services;

namespace Vigia.API.Middlewares;

public class AuthUserMiddleware(IRevokedTokensCacheService revokedTokensCacheService, JwtConverterService jwtConverterService) : IMiddleware
{
    private readonly IRevokedTokensCacheService _revokedTokensCacheService = revokedTokensCacheService;
    private readonly JwtConverterService _jwtConverterService = jwtConverterService;

    private static readonly string[] _allowedPaths = new string[] { "login", "register" };


    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {

        string route = context.Request.Path.ToString().Split("/").Last();

        if (_allowedPaths.Contains(route))
        {
            await next(context);
            return;
        }

        string? accessToken = context.Request.Headers["Authorization"].FirstOrDefault()?.Split(" ").Last();

        if (string.IsNullOrEmpty(accessToken))
        {
            await UnauthorizedResponse(context);
            return;
        }

        bool isValidToken = _jwtConverterService.Decode(accessToken, out var decodedProperties);

        if (!isValidToken)
        {
            await UnauthorizedResponse(context);
            return;
        }

        context.Items["userId"] = decodedProperties!.Value.userId;
        context.Items["roles"] = decodedProperties.Value.roles;
        context.Items["tokenId"] = decodedProperties.Value.tokenId;
        context.Items["expiresAt"] = decodedProperties.Value.expiresAt;

        await next(context);
    }


    private async Task UnauthorizedResponse(HttpContext context)
    {
        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsync(JsonSerializer.Serialize(new { error = "Unauthorized" }));
    }
}
