
using System.Text.Json;
using Vigia.API.Models.Helpers;

namespace Vigia.API.Middlewares;

public class AuthUserMiddleware : IMiddleware
{
    private static readonly string[] _allowedPaths = new string[] { "/login", "/register" };


    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        string? accessToken = context.Request.Headers["Authorization"].FirstOrDefault()?.Split(" ").Last();

        if (string.IsNullOrEmpty(accessToken) || !_allowedPaths.Contains(context.Request.PathBase.ToString()))
        {
            await UnauthorizedResponse(context);
            return;
        }

        var convertedToken = JwtConverter.Decode(accessToken);

        if (convertedToken.userId == Guid.Empty ||
            convertedToken.roles.Count == 0)
        {
            await UnauthorizedResponse(context);
            return;
        }

        context.Items["userId"] = convertedToken.userId;
        context.Items["roles"] = convertedToken.roles;

        await next(context);
    }

    private async Task UnauthorizedResponse(HttpContext context)
    {
        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsync(JsonSerializer.Serialize(new { error = "Unauthorized" }));
    }
}
