using System.Text.Json;
using Vigia.API.Models.Helpers;

namespace Vigia.API.Middlewares;

public class AuthUserMiddleware(IConfiguration configuration) : IMiddleware
{
    private readonly IConfiguration _configuration = configuration;
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

        if (!JwtConverter.ValidateToken(_configuration, accessToken))
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
